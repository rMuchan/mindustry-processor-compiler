from abc import ABC, abstractmethod
from typing import Optional, List, Dict

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
    index: Optional['Expression'] = None
    value: 'Expression'

    def generate(self):
        if self.index is None:
            self.value.generate_to(self.target)
        else:
            value_var = self.value.generate()
            index_var = self.index.generate()
            _emit(f'write {value_var} {self.target} {index_var}')


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
            self.value.generate_to(f'$ret${name}')
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


class Expression(ABC):
    # not all bool expressions must be converted to 0/1 immediately, e.g. operands of logical operators.
    # the next two fields attempt to convert them as needed.
    type_is_bool: bool = False  # whether this expr is expected to return a bool value
    value_is_bool: bool = False  # whether this expr actually returns a bool value

    def convert_to_bool(self) -> 'Expression':
        """
        Append an instruction to convert the value if type is bool but value is not, otherwise do nothing.
        `value_is_bool` of result is set to True if type is bool.
        :return: The new expression if converted, otherwise `self`.
        """
        if self.type_is_bool and not self.value_is_bool:
            exp = OperationExpr('not', self, BaseExpr.zero(), True, convert_operand=False)
            exp.value_is_bool = True
            return exp
        else:
            return self

    def generate(self) -> str:
        var = _get_next_temp()
        self.generate_to(var)
        return var

    @abstractmethod
    def generate_to(self, target: str): pass

    def generate_condition(self, label: 'Label', invert: bool):
        var = self.generate()
        cond = 'equal' if invert else 'notEqual'
        _emit(f'jump {{}} {cond} {var} 0', label)


class BaseExpr(Expression):
    value: str

    @staticmethod
    def zero():
        exp = BaseExpr('0')
        exp.type_is_bool = True
        exp.value_is_bool = True
        return exp

    def __init__(self, val: str):
        self.value = val

    def generate(self) -> str:
        return self.value

    def generate_to(self, target: str):
        _emit(f'set {target} {self.value}')


class OperationExpr(Expression):
    inst: str
    opr1: Expression
    opr2: Expression

    def __init__(self, inst: str, opr1: Expression, opr2: Expression,
                 set_bool: Optional[bool], convert_operand: bool = True):
        """
        Create an expression object representing `opr1 inst opr2`. `type_is_bool` of the new expression is set to False.
        :param inst: Operation to perform. Should be a valid option for Mindustry `operation` instruction.
        :param opr1: The first operand.
        :param opr2: The second operand.
        :param set_bool: Whether the new expr returns a bool value.
                         If given `None`, the new expr returns a bool value iff both operands return bool values.
        :param convert_operand: Whether the operands should be converted if their types are bool but values are not.
        """
        if convert_operand:
            opr1 = opr1.convert_to_bool()
            opr2 = opr2.convert_to_bool()
        self.inst = inst
        self.opr1 = opr1
        self.opr2 = opr2
        if set_bool is None:
            self.value_is_bool = opr1.value_is_bool and opr2.value_is_bool
        else:
            self.value_is_bool = set_bool

    def generate_to(self, target: str):
        var1 = self.opr1.generate()
        var2 = self.opr2.generate()
        if target != '_':
            _emit(f'op {self.inst} {target} {var1} {var2}')

    def generate_condition(self, label: 'Label', invert: bool):
        invert_map = {
            'equal': 'notEqual',
            'notEqual': 'equal',
            'lessThan': 'greaterThanEq',
            'lessThanEq': 'greaterThan',
            'greaterThan': 'lessThanEq',
            'greaterThanEq': 'lessThan'
        }

        if self.inst in invert_map:  # comparison
            var1 = self.opr1.generate()
            var2 = self.opr2.generate()
            cond = invert_map[self.inst] if invert else self.inst
            _emit(f'jump {{}} {cond} {var1} {var2}', label)
        else:  # computation
            super().generate_condition(label, invert)


class FunctionExpr(Expression):
    func: Function
    args: List[Expression]

    def __init__(self, func: Function, args: List[Expression]):
        self.func = func
        self.args = args

    def generate_to(self, target: str):
        tmp_vars = []
        for arg in self.args:
            var = arg.generate()
            tmp_vars.append(var)
        for param_name, var in zip(self.func.param, tmp_vars):
            _emit(f'set {param_name} {var}')
        _emit(f'op add $ra${self.func.name} @counter 1')
        _emit('jump {} always', self.func.home_label)
        if target != '_':
            _emit(f'set {target} $ret${self.func.name}')


class MemoryLoadExpr(Expression):
    cell: str
    index: Expression

    def __init__(self, cell: str, index: Expression):
        self.cell = cell
        self.index = index

    def generate_to(self, target: str):
        var = self.index.generate()
        if target != '_':
            _emit(f'read {target} {self.cell} {var}')


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
