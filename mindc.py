import sys
from typing import TextIO

import g
import syntax


def main():
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} source_file', file=sys.stderr)
        return

    if sys.argv[1] == '-':
        do_compile(sys.stdin)
    else:
        try:
            with open(sys.argv[1]) as f:
                do_compile(f)
        except IOError:
            print('Failed to open source file.', file=sys.stderr)


def do_compile(file: TextIO):
    g.file = file

    try:
        prog = syntax.program()
    except g.ParseError as e:
        print(f'Line {e.line} Character {e.pos}: {e.message}', file=sys.stderr)
        return

    prog.generate()
    for inst, label in g.code:
        if label is None:
            print(inst)
        else:
            print(inst.format(label.inst))


if __name__ == '__main__':
    main()
