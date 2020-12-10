# Language Definition

## Syntax

The language processed by this compiler, namely MindC, is defined as follows:

```
Program := { Function } MainProcedure
Function := 'def' Identifier '(' ParamList ')' '{' StmtList '}'
ParamList := [ Identifier { ',' Identifier } ]
StmtList := { Statement }
Statement := [ AssignStmt | CondStmt | LoopStmt | ReturnStmt | 'break' | 'continue' ] [ ';' ] | RawStmt | '{' StmtList '}'
AssignStmt := Identifier '=' Expression
CondStmt := 'if' '(' Expression ')' Statement [ 'else' Statement ]
LoopStmt := 'while' '(' Expression ')' Statement
ReturnStmt := 'return' [ Expression ]
Expression := LOrExp
LOrExp := LAndExp { '||' LAndExp }
LAndExp := BOrExp  { '&&' BOrExp }
BOrExp := BXorExp { '|' BXorExp }
BXorExp := BAndExp { '^' BAndExp }
BAndExp := EqExp { '&' EqExp }
EqExp := CompExp { ( '==' | '!=' ) CompExp }
CompExp := ShiftExp { ( '<' | '>' | '<=' | '>=' ) ShiftExp }
ShiftExp := PlusExp { ( '<<' | '>>' ) PlusExp }
PlusExp := MulExp { ( '+' | '-' ) MulExp }
MulExp := PowExp { ( '*' | '/' | '%' | '//' ) PowExp }
PowExp := UnaryExp { '**' UnaryExp }
UnaryExp := { '-' | '~' | '!' } BaseExp
BaseExp := Identifier | '(' Expression ')' | NumLiteral | Call
Call := Identifier '(' ArgList ')'
ArgList := [ Expression { ',' Expression } ]
MainProcedure := StmtList
```

Where:

- An `Identifier` is an sequence of letters, digits and underscores. The initial element shall not be a digit.
- A `NumLiteral` is a sequence of digits, with an optional decimal point.
- `RawStmt` is discussed in the following section.

### Raw Statements

It just doesn't make sense to create a different syntax for each functionality supported by Mindustry, so we introduce raw statements. A raw statement starts with a `$` (and optional whitespaces), and terminates at the end of that line. Characters between them are output untransformed.

This feature implies that MindC is almost compatible with native Mindustry language: simply add a `$` at the beginning of each line, and you got a valid MindC program. That operation can be easily done with editors like VS Code or command line tools like sed.

### Semicolons

Semicolons are not required at the end of statements, but it's OK if you wrote one. A lone semicolon is interpreted as an empty statement.

However, raw statements cannot be ended by a semicolon, because they terminates at the end of line. Any semicolons on that line are output as a part of the instruction.

### Comments

A comment starts with a `#` and terminates at the end of that line. Comments are ignored while parsing source file.

Comments cannot be on the same line as raw statements.

## Data Types

The values in variables can be numbers or objects. Strings are not supported because they can only be used in `print` instructions, as a part of a raw statement.

When an operation needs an object but is given a number, it will be converted to `null`.

When an operation needs a number but is given an object, it will be converted to 1 if the object isn't `null`, otherwise 0.

## Builtin variables

There are several variables/constants provided by the processor, all of which start with an `@`. They are treated as identifiers as well.

## Builtin functions

MindC provides several functions. They are actually compiled to `operation` instructions.

Unary functions:

- `abs`, `sin`, `cos`, `tan`, `floor`, `ceil`, `sqrt`: As their names state
- `lg`: Base-10 logarithm
- `ln`: Natural logarithm
- `rand(x)`: Generate a random number between 0 and x

Binary functions:

- `max`, `min`, `atan2`: As their names state
- `dst(x, y)`: Compute `sqrt(x*x+y*y)`

All trigonometric functions are in degrees.

## Note

- A lowercase word followed by an integer is a valid identifier, but may be buildings connected to the processor. Use with care.
- Values assigned to variable `_` will be ignored.
- Logical shortcut is not supported, i.e. all clauses will be evaluated.
- Function invocation statements are not supported. Assign its return value to `_` instead.
- Functions are not ready for invocation until fully defined, which implies recursion is not supported.