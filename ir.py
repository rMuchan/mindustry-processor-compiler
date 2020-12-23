from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Tuple, Union

import g


class Program:
    functions: Dict[str, 'Function']
    main_procedure: List['Statement']

    def __init__(self):
        self.functions = {}

    def generate(self):
        for stmt in self.main_procedure:
            stmt.generate()
        if self.functions:
            _emit('end')
            for func in self.functions.values():
                func.generate()
        if len(g.code) == Label.last_label:
            _emit('noop')


class Function:
    home_label: 'Label'
    name: str
    param: List[str]
    statements: List['Statement']

    def __init__(self):
        self.home_label = Label()
        self.param = []

    def generate(self):
        self.home_label.generate()
        for stmt in self.statements:
            stmt.generate()


class Statement(ABC):
    _returns_cache: Optional[bool] = None

    @abstractmethod
    def generate(self): pass

    def returns(self) -> bool:
        if self._returns_cache is None:
            self._returns_cache = self._returns()
        return self._returns_cache

    def _returns(self) -> bool:
        return False


class AssignStmt(Statement):
    target: str
    value: 'Expression'

    def generate(self):
        self.value.generate(self.target)


class CondStmt(Statement):
    condition: 'Expression'
    match: Statement
    mismatch: Optional[Statement] = None

    def generate(self):
        if self.mismatch is not None:
            mismatch_label = Label()
            end_label = Label()
            self.condition.generate_condition(mismatch_label, invert=True)
            self.match.generate()
            _emit('jump {} always', end_label)
            mismatch_label.generate()
            self.mismatch.generate()
            end_label.generate()
        else:
            end_label = Label()
            self.condition.generate_condition(end_label, invert=True)
            self.match.generate()
            end_label.generate()

    def _returns(self) -> bool:
        return self.mismatch and self.match.returns() and self.mismatch.returns()


class LoopStmt(Statement):
    home_label: 'Label'
    end_label: 'Label'
    condition: 'Expression'
    body: Statement

    def __init__(self):
        self.home_label = Label()
        self.end_label = Label()

    def generate(self):
        self.home_label.generate()
        self.condition.generate_condition(self.end_label, invert=True)
        self.body.generate()
        _emit('jump {} always', self.home_label)
        self.end_label.generate()


class ReturnStmt(Statement):
    value: Optional['Expression'] = None
    belong_func: Function

    def generate(self):
        name = self.belong_func.name
        if self.value is not None:
            self.value.generate(f'$ret${name}')
        _emit(f'set @counter $ra${name}')

    def _returns(self) -> bool:
        return True


class JumpStmt(Statement):
    target: 'Label'

    def generate(self):
        _emit('jump {} always', self.target)


class RawStmt(Statement):
    inst: str

    def generate(self):
        _emit(self.inst)


class CompoundStmt(Statement):
    stmts: List[Statement]

    def generate(self):
        for stmt in self.stmts:
            stmt.generate()

    def _returns(self) -> bool:
        return any(x.returns() for x in self.stmts)


class EmptyStmt(Statement):
    def generate(self):
        pass


class Expression:
    # normal instruction: (instruction name, operand 1, operand 2)
    # the un-parameterized "tuple" is a reference to another node
    NormalInstNode = Tuple[str, Union[str, tuple], Union[str, tuple]]
    # function call: (function name, arguments, None)
    FuncCallNode = Tuple[Function, List['Expression'], None]
    NodeType = Union[str, NormalInstNode, FuncCallNode]

    value: NodeType
    # not all bool expressions must be converted to 0/1 immediately, e.g. operands of logical operators.
    # the next two fields attempt to convert them as needed.
    type_is_bool: bool = False  # whether this expr is expected to return a bool value
    value_is_bool: bool = False  # whether this expr actually returns a bool value

    def __init__(self, value: Union[NodeType, Function], args: List['Expression'] = None):
        if args is None:
            self.value = value
        else:
            assert isinstance(value, Function)
            self.value = (value, args, None)

    @staticmethod
    def zero():
        exp = Expression('0')
        exp.type_is_bool = True
        exp.value_is_bool = True
        return exp

    def convert_to_bool(self) -> 'Expression':
        """
        Append an instruction to convert the value if type is bool but value is not, otherwise do nothing.
        `value_is_bool` of result is set to True if type is bool.
        :return: The new expression if converted, otherwise `self`.
        """
        if self.type_is_bool and not self.value_is_bool:
            exp = self.combine('not', Expression.zero(), True, convert_operand=False)
            exp.value_is_bool = True
            return exp
        else:
            return self

    def combine(self, op: str, right: 'Expression', set_bool: Optional[bool],
                convert_operand: bool = True) -> 'Expression':
        """
        Create an expression object representing `self op right`. `type_is_bool` of the new expression is set to False.
        :param op: Operation to perform. Should be a valid option for Mindustry `operation` instruction.
        :param right: The second operand.
        :param set_bool: Whether the new expr returns a bool value.
                         If given `None`, the new expr returns a bool value iff both operands return bool values.
        :param convert_operand: Whether the operands should be converted if their types are bool but values are not.
        :return: The new expression.
        """
        if convert_operand:
            left = self.convert_to_bool()
            right = right.convert_to_bool()
        else:
            left = self
        exp = Expression((op, self.value, right.value))
        if set_bool is None:
            exp.value_is_bool = left.value_is_bool and right.value_is_bool
        else:
            exp.value_is_bool = set_bool
        return exp

    def generate(self, target: str):
        Expression._generate_node(target, self.value)

    def generate_condition(self, label: 'Label', invert: bool):
        if isinstance(self.value, str):
            cond = 'equal' if invert else 'notEqual'
            _emit(f'jump {{}} {cond} {self.value} 0', label)
            return

        invert_map = {
            'equal': 'notEqual',
            'notEqual': 'equal',
            'lessThan': 'greaterThanEq',
            'lessThanEq': 'greaterThan',
            'greaterThan': 'lessThanEq',
            'greaterThanEq': 'lessThan'
        }

        inst, opr1, opr2 = self.value
        if inst in invert_map:  # last instruction is comparison
            var1 = Expression._generate_child(opr1)
            var2 = Expression._generate_child(opr2)
            cond = invert_map[inst] if invert else inst
            _emit(f'jump {{}} {cond} {var1} {var2}', label)
        else:  # last instruction is computation or function invocation
            var = _get_next_temp()
            Expression._generate_node(var, self.value)
            cond = 'equal' if invert else 'notEqual'
            _emit(f'jump {{}} {cond} {var} 0', label)

    @staticmethod
    def _generate_node(target: str, expr: NodeType):
        if isinstance(expr, str):
            _emit(f'set {target} {expr}')
            return
        inst, opr1, opr2 = expr
        if isinstance(inst, str):  # instruction
            opr1: Union[str, tuple]
            opr2: Union[str, tuple]
            var1 = Expression._generate_child(opr1)
            var2 = Expression._generate_child(opr2)
            if target != '_':
                _emit(f'op {inst} {target} {var1} {var2}')
        else:  # function
            inst: Function
            opr1: List['Expression']
            tmp_vars = []
            for arg in opr1:
                var = _get_next_temp()
                arg.generate(var)
                tmp_vars.append(var)
            for param_name, var in zip(inst.param, tmp_vars):
                _emit(f'set {param_name} {var}')
            _emit(f'op add $ra${inst.name} @counter 1')
            _emit('jump {} always', inst.home_label)
            if target != '_':
                _emit(f'set {target} $ret${inst.name}')

    @staticmethod
    def _generate_child(opr: NodeType) -> str:
        if isinstance(opr, str):
            return opr
        var = _get_next_temp()
        Expression._generate_node(var, opr)
        return var


class Label:
    inst: int
    last_label: int = -1

    def generate(self):
        self.inst = len(g.code)
        Label.last_label = self.inst


_temp_var_num = 0


def _get_next_temp() -> str:
    global _temp_var_num
    _temp_var_num += 1
    return f'$tmp${_temp_var_num}'


def _emit(instruction: str, label: Label = None):
    g.code.append((instruction, label))
