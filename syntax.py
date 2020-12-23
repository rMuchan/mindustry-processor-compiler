from typing import Callable

import lex
from ir import *
from lex import Token, TokenType


def program() -> Program:
    prog = Program()
    g.context.append(prog)
    while _peek() == TokenType.Def:
        f = function()
        prog.functions[f.name] = f
    prog.main_procedure = stmt_list()
    _expect(TokenType.EOF)
    g.context.pop()
    return prog


def function() -> Function:
    func = Function()
    _expect(TokenType.Def)
    tk = _expect(TokenType.Identifier)
    func.name = tk.value
    if func.name in g.context[0].functions or func.name in _builtin_functions:
        raise g.ParseError(f'Redefinition of function {func.name}.', tk.line, tk.pos)
    _expect(TokenType.LPara)
    if _peek() != TokenType.RPara:
        is_first = True
        while is_first or _peek() == TokenType.Comma:
            if not is_first:
                lex.read()
            is_first = False
            tk = _expect(TokenType.Identifier)
            param_name = tk.value
            if param_name in func.param:
                raise g.ParseError(f'Redefinition of parameter {param_name}.', tk.line, tk.pos)
            func.param.append(param_name)
    _expect(TokenType.RPara)
    _expect(TokenType.LBrace)
    g.context.append(func)
    func.statements = stmt_list()
    if not any(x.returns() for x in func.statements):
        stmt = ReturnStmt()
        stmt.belong_func = func
        func.statements.append(stmt)
    g.context.pop()
    _expect(TokenType.RBrace)
    return func


def stmt_list() -> List[Statement]:
    sl = []
    while _peek() in {TokenType.Identifier, TokenType.If, TokenType.While, TokenType.Return, TokenType.Break,
                      TokenType.Continue, TokenType.Semicolon, TokenType.RawStmt, TokenType.LBrace}:
        s = statement()
        sl.append(s)
    return sl


def statement() -> Statement:
    parser, accept_semicolon = {
        TokenType.Identifier: (assign_stmt, True),
        TokenType.If: (cond_stmt, False),
        TokenType.While: (loop_stmt, False),
        TokenType.Return: (return_stmt, True),
        TokenType.Break: (loop_ctrl_stmt, True),
        TokenType.Continue: (loop_ctrl_stmt, True),
        TokenType.Semicolon: (EmptyStmt, True),
        TokenType.RawStmt: (raw_stmt, False),
        TokenType.LBrace: (compound_stmt, False)
    }[_peek()]
    s = parser()
    if accept_semicolon and _peek() == TokenType.Semicolon:
        lex.read()
    return s


def assign_stmt() -> Statement:
    stmt = AssignStmt()
    stmt.target = _expect(TokenType.Identifier).value
    if _peek() == TokenType.LBracket:
        lex.read()
        stmt.index = expression().convert_to_bool()
        _expect(TokenType.RBracket)
    _expect(TokenType.AssignOp)
    stmt.value = expression().convert_to_bool()
    return stmt


def cond_stmt() -> Statement:
    stmt = CondStmt()
    _expect(TokenType.If)
    _expect(TokenType.LPara)
    stmt.condition = expression()
    _expect(TokenType.RPara)
    stmt.match = statement()
    if _peek() == TokenType.Else:
        lex.read()
        stmt.mismatch = statement()
    return stmt


def loop_stmt() -> Statement:
    stmt = LoopStmt()
    _expect(TokenType.While)
    _expect(TokenType.LPara)
    stmt.condition = expression()
    _expect(TokenType.RPara)
    g.context.append(stmt)
    stmt.body = statement()
    g.context.pop()
    return stmt


def return_stmt() -> Statement:
    stmt = ReturnStmt()
    tk = _expect(TokenType.Return)
    func = g.context[1] if len(g.context) > 1 else None
    if not isinstance(func, Function):
        raise g.ParseError('Unexpected return.', tk.line, tk.pos)
    stmt.belong_func = func
    if _peek() in {TokenType.SubOp, TokenType.BNotOp, TokenType.LNotOp, TokenType.Identifier,
                   TokenType.LPara, TokenType.Number}:
        stmt.value = expression().convert_to_bool()
    return stmt


def loop_ctrl_stmt() -> Statement:
    stmt = JumpStmt()
    tk = lex.read()
    loop = g.context[-1]
    if not isinstance(loop, LoopStmt):
        raise g.ParseError('Unexpected loop control statement.', tk.line, tk.pos)
    if tk.type_ == TokenType.Break:
        stmt.target = loop.end_label
    elif tk.type_ == TokenType.Continue:
        stmt.target = loop.home_label
    else:  # pragma: no cover
        raise g.ParseError('Invalid loop control statement.', tk.line, tk.pos)
    return stmt


def raw_stmt() -> Statement:
    stmt = RawStmt()
    stmt.inst = _expect(TokenType.RawStmt).value
    return stmt


def compound_stmt() -> Statement:
    stmt = CompoundStmt()
    _expect(TokenType.LBrace)
    stmt.stmts = stmt_list()
    _expect(TokenType.RBrace)
    return stmt


def expression() -> Expression:
    return l_or_exp()


def _create_expr_parser(sub_expr_parser: Callable[[], Expression], set_bool: Optional[bool], ops: Dict[TokenType, str],
                        type_is_bool: bool = False, convert_operand: bool = True) -> Callable[[], Expression]:
    def parser() -> Expression:
        exp = sub_expr_parser()
        while _peek() in ops:
            op = ops[lex.read().type_]
            exp = exp.combine(op, sub_expr_parser(), set_bool, convert_operand)
            if type_is_bool:
                exp.type_is_bool = True
        return exp

    return parser


def unary_exp() -> Expression:
    operations = []
    double_not = ()
    while _peek() in {TokenType.AddOp, TokenType.SubOp, TokenType.BNotOp, TokenType.LNotOp}:
        op = lex.read().type_
        if op == TokenType.AddOp:
            pass
        elif operations and operations[-1] == op:
            if op == TokenType.LNotOp:
                operations[-1] = double_not
            else:
                operations.pop()
        elif op == TokenType.LNotOp and operations and operations[-1] is double_not:
            operations[-1] = op
        else:
            operations.append(op)
    exp = base_exp()
    for op in reversed(operations):
        if op == TokenType.SubOp:
            exp = Expression.zero().combine('sub', exp, False)
        elif op == TokenType.BNotOp:
            exp = exp.combine('not', Expression.zero(), False)
        elif op == TokenType.LNotOp:
            exp = exp.combine('equal', Expression.zero(), True, convert_operand=False)
            exp.type_is_bool = True
        elif op is double_not:
            exp = exp.combine('notEqual', Expression.zero(), True, convert_operand=False)
            exp.type_is_bool = True
    return exp


pow_exp = _create_expr_parser(unary_exp, None, {TokenType.PowOp: 'pow'})
mul_exp = _create_expr_parser(pow_exp, None, {
    TokenType.MulOp: 'mul',
    TokenType.DivOp: 'div',
    TokenType.ModOp: 'mod',
    TokenType.FloorDivOp: 'idiv'
})
plus_exp = _create_expr_parser(mul_exp, False, {TokenType.AddOp: 'add', TokenType.SubOp: 'sub'})
shift_exp = _create_expr_parser(plus_exp, False, {TokenType.LShiftOp: 'shl', TokenType.RShiftOp: 'shr'})
comp_exp = _create_expr_parser(shift_exp, True, {
    TokenType.LtOp: 'lessThan',
    TokenType.GtOp: 'greaterThan',
    TokenType.LeqOp: 'lessThanEq',
    TokenType.GeqOp: 'greaterThanEq'
}, True)
eq_exp = _create_expr_parser(comp_exp, True, {TokenType.EqOp: 'equal', TokenType.NeqOp: 'notEqual'}, True)
b_and_exp = _create_expr_parser(eq_exp, None, {TokenType.BAndOp: 'and'})
b_xor_exp = _create_expr_parser(b_and_exp, None, {TokenType.BXorOp: 'xor'})
b_or_exp = _create_expr_parser(b_xor_exp, None, {TokenType.BOrOp: 'or'})
l_and_exp = _create_expr_parser(b_or_exp, True, {TokenType.LAndOp: 'land'}, True, convert_operand=False)
l_or_exp = _create_expr_parser(l_and_exp, None, {TokenType.LOrOp: 'or'}, True, convert_operand=False)


def base_exp() -> Expression:
    type_ = _peek()
    if type_ == TokenType.LPara:
        lex.read()
        exp = expression()
        _expect(TokenType.RPara)
        return exp
    elif type_ == TokenType.Number:
        val = lex.read().value
        return Expression(val)
    elif type_ == TokenType.Identifier:
        tk = lex.read()
        if _peek() == TokenType.LPara:
            return call(tk)
        elif _peek() == TokenType.LBracket:
            lex.read()
            index = expression().convert_to_bool()
            _expect(TokenType.RBracket)
            return Expression.memory_load(tk.value, index)
        else:
            return Expression(tk.value)
    else:
        tk = lex.read()
        raise g.ParseError('Invalid expression.', tk.line, tk.pos)


def call(func_name_tk: Token) -> Expression:
    # determine if the function is builtin
    func_name = func_name_tk.value
    prog: Program = g.context[0]
    func = prog.functions.get(func_name)
    if func is not None:
        param_num = len(func.param)
    elif func_name in _builtin_functions:
        param_num = _builtin_functions[func_name]
    else:
        raise g.ParseError('Unknown function.', func_name_tk.line, func_name_tk.pos)

    # parse argument list
    args: List[Expression] = []
    _expect(TokenType.LPara)
    if _peek() != TokenType.RPara:
        is_first = True
        while is_first or _peek() == TokenType.Comma:
            if not is_first:
                lex.read()
            is_first = False
            arg = expression().convert_to_bool()
            args.append(arg)
    r_para = _expect(TokenType.RPara)

    # check the number of arguments
    if len(args) != param_num:
        raise g.ParseError('Expect {} argument{}, got {}.'.format(param_num, 's' if param_num != 1 else '', len(args)),
                           r_para.line, r_para.pos)

    # generate IR
    if func is None:  # builtin function
        exp = args[0]
        if exp.value_is_bool and func_name in _builtin_bool_identity:
            return exp
        set_bool = None if func_name in _builtin_preserve_bool else False
        second_operand = args[1] if param_num == 2 else Expression.zero()
        return exp.combine(func_name, second_operand, set_bool)
    else:  # custom function
        return Expression(func, args)


_builtin_functions = {
    'abs': 1, 'sin': 1, 'cos': 1, 'tan': 1, 'floor': 1, 'ceil': 1, 'sqrt': 1, 'log10': 1, 'log': 1, 'rand': 1,
    'max': 2, 'min': 2, 'atan2': 2, 'dst': 2, 'noise': 2
}
_builtin_bool_identity = {'abs', 'floor', 'ceil', 'sqrt'}
_builtin_preserve_bool = {'max', 'min'}


def _expect(type_: TokenType) -> Token:
    tk = lex.read()
    if tk.type_ != type_:
        name = f'"{type_.value}"' if isinstance(type_.value, str) else type_.name
        raise g.ParseError(f'Expected {name}.', tk.line, tk.pos)
    return tk


def _peek() -> TokenType:
    return lex.peek().type_
