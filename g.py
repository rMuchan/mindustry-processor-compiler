from typing import TextIO

file: TextIO
context: list = []


class ParseError(Exception):
    def __init__(self, message: str, line: int, pos: int):
        self.message = message
        self.line = line
        self.pos = pos
