from typing import Optional, List, Dict, Tuple, Union


class Program:
    functions: Dict[str, 'Function']
    main_procedure: List['Statement']

    def __init__(self):
        self.functions = {}


class Function:
    home_label: 'Label'
    name: str
    param: List[str]
    statements: List['Statement']

    def __init__(self):
        self.home_label = Label()
        self.param = []


class Statement:
    ...


class AssignStmt(Statement):
    target: str
    value: 'Expression'


class CondStmt(Statement):
    condition: 'Expression'
    match: Statement
    mismatch: Optional[Statement] = None


class LoopStmt(Statement):
    home_label: 'Label'
    end_label: 'Label'
    condition: 'Expression'
    body: Statement

    def __init__(self):
        self.home_label = Label()
        self.end_label = Label()


class ReturnStmt(Statement):
    value: Optional['Expression'] = None
    belong_func: Function


class JumpStmt(Statement):
    target: 'Label'


class RawStmt(Statement):
    inst: str


class CompoundStmt(Statement):
    stmts: List[Statement]


class EmptyStmt(Statement):
    pass


class Expression:
    # normal instruction: (instruction name, operand 1, operand 2)
    # the un-parameterized "tuple" is a reference to another node
    NormalInstNode = Tuple[str, Union[str, tuple], Union[str, tuple]]
    # function call: (None, function name, arguments)
    FuncCallNode = Tuple[None, str, List[Tuple[str, 'Expression']]]

    value: Union[str, NormalInstNode, FuncCallNode]
    # not all bool expressions must be converted to 0/1 immediately, e.g. operands of logical operators.
    # the next two fields attempt to convert them as needed.
    type_is_bool: bool = False  # whether this expr is expected to return a bool value
    value_is_bool: bool = False  # whether this expr actually returns a bool value

    def __init__(self, value: Union[str, NormalInstNode], args: List[Tuple[str, 'Expression']] = None):
        if args is None:
            self.value = value
        else:
            assert isinstance(value, str)
            self.value = (None, value, args)

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


class Label:
    ...
