from typing import TextIO, List, Tuple, Any

file: TextIO
context: list = []
code: List[Tuple[str, Any]] = []  # type of the 2nd component is Optional[ir.Label]


class ParseError(Exception):
    def __init__(self, message: str, line: int, pos: int):
        self.message = message
        self.line = line
        self.pos = pos
