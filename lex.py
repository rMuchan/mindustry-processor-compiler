from dataclasses import dataclass
from enum import Enum, auto, unique
from typing import Optional, List

import g


@unique
class TokenType(Enum):
    Identifier = auto()
    Number = auto()
    RawStmt = auto()
    EOF = auto()

    Def = 'def'
    If = 'if'
    Else = 'else'
    While = 'while'
    Break = 'break'
    Continue = 'continue'
    Return = 'return'

    LPara = '('
    RPara = ')'
    LBracket = '['
    RBracket = ']'
    LBrace = '{'
    RBrace = '}'
    Comma = ','
    Semicolon = ';'

    AssignOp = '='
    LAndOp = '&&'
    LOrOp = '||'
    LNotOp = '!'
    BAndOp = '&'
    BOrOp = '|'
    BXorOp = '^'
    BNotOp = '~'
    EqOp = '=='
    NeqOp = '!='
    LtOp = '<'
    GtOp = '>'
    LeqOp = '<='
    GeqOp = '>='
    LShiftOp = '<<'
    RShiftOp = '>>'
    AddOp = '+'
    SubOp = '-'
    MulOp = '*'
    DivOp = '/'
    ModOp = '%'
    FloorDivOp = '//'
    PowOp = '**'


@dataclass
class Token:
    type_: TokenType
    value: Optional[str]
    line: int
    pos: int


_operators = {v.value: v for v in TokenType if isinstance(v.value, str) and not v.value.isalpha()}
_keywords = {v.value: v for v in TokenType if isinstance(v.value, str) and v.value.isalpha()}

_tokens: List[Token] = []
_line_num: int = 1


def peek() -> Token:
    _fill_tokens()
    return _tokens[0]


def read() -> Token:
    _fill_tokens()
    return _tokens.pop(0)


def _fill_tokens():
    global _line_num

    while not _tokens:
        line = g.file.readline()
        if line:
            _tokenize_line(line)
            _line_num += 1
        else:
            _add_token(TokenType.EOF, None, 0)


def _tokenize_line(line: str):
    line += ' '  # help peeking
    i = 0
    while True:
        while i < len(line) and line[i].isspace():
            i += 1
        if i == len(line):
            break
        if line[i:i + 2] in _operators:
            _add_token(_operators[line[i:i + 2]], None, i)
            i += 2
        elif line[i] in _operators:
            _add_token(_operators[line[i]], None, i)
            i += 1
        elif line[i].isdigit() or line[i] == '.':
            start = i
            accept_point = True
            while line[i].isdigit() or (accept_point and line[i] == '.'):
                if line[i] == '.':
                    accept_point = False
                i += 1
            _add_token(TokenType.Number, line[start:i], start)
        elif line[i].isalpha() or line[i] == '_' or line[i] == '@':
            start = i
            i += 1
            while line[i].isalnum() or line[i] == '_':
                i += 1
            keyword_type = _keywords.get(line[start:i])
            if keyword_type is not None:
                _add_token(keyword_type, None, start)
            else:
                _add_token(TokenType.Identifier, line[start:i], start)
        elif line[i] == '$':
            _add_token(TokenType.RawStmt, line[i + 1:].strip(), i)
            break
        elif line[i] == '#':
            break
        else:
            raise g.ParseError('Invalid token', _line_num, i + 1)


# `index` is 0-based
def _add_token(type_: TokenType, value: Optional[str], index: int):
    _tokens.append(Token(type_, value, _line_num, index + 1))
