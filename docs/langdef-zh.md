# 语言定义

## 语法

本编译器接受的语言（MindC）定义如下：

```
Program := { Function } MainProcedure
Function := 'def' Identifier '(' ParamList ')' '{' StmtList '}'
ParamList := [ Identifier { ',' Identifier } ]
StmtList := { Statement }
Statement := [ AssignStmt | ReturnStmt | 'break' | 'continue' ] [ ';' ] | CondStmt | LoopStmt | RawStmt | '{' StmtList '}'
AssignStmt := LValue '=' Expression
LValue := Identifier [ '[' Expression ']' ]
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
UnaryExp := { '+' | '-' | '~' | '!' } BaseExp
BaseExp := LValue | '(' Expression ')' | NumLiteral | Call
Call := Identifier '(' ArgList ')'
ArgList := [ Expression { ',' Expression } ]
MainProcedure := StmtList
```

其中：

- 标识符（`Identifier`）可以由字母、数字和下划线组成，第一个字符不能是数字。
- 数值字面量（`NumLiteral`）是一串数字，其中可以包含一个小数点。
- 原始语句（`RawStmt`）详见下一节。

### 原始语句

为Mindustry支持的每个功能都设计语法并没有意义，所以本语言引入了原始语句。原始语句以`$`开头，到行尾结束，两者之间的字符会直接输出。

这个特性使MindC几乎与Mindustry原生语言兼容：只要在Mindustry程序的每一行开头加上一个`$`，就可以得到一个合法的MindC程序。这种操作很容易使用编辑器（如VS Code）或命令行工具（如sed）完成。

### 内存访问

MindC使用数组语法操作内存元/内存库。方括号前的标识符应当是一个连接到处理器的内存元/内存库。例如，下列源代码：

```
temp = cell1[42]
bank1[0] = temp
```

会被编译为：

```
read temp cell1 42
write temp bank1 0
```

### 分号

语句结尾不要求有分号，但写上分号并不是错误。单独出现的分号会被解析为一条空语句。

原始语句不能以分号结尾。在`$`之后的分号会作为原始语句的一部分直接输出。

### 注释

注释以`#`开头，到行尾结束。解析源文件时会忽略注释。

注释不能在原始语句的同一行上，原因同上。

## 数据类型

变量中存储的数据类型可以是数字或对象。MindC不支持字符串，因为字符串只可能作为原始语句的一部分在`print`指令中出现。

当一个操作需要对象作为操作数，但提供了数字时，数字会被转换为`null`。当一个操作需要数字作为操作数，但提供了对象时，非`null`的对象会被转换为1，`null`会被转换为0。

## 内置变量

处理器提供了一些以`@`开头的变量，它们也被视为合法的标识符。

## 内置函数

MindC提供了下列函数。它们实际上会被编译为`operation`指令。

一元函数:

- `abs`, `sin`, `cos`, `tan`, `floor`, `ceil`, `sqrt`：如名称所述
- `log10`：以10为底的对数
- `log`：自然对数
- `rand(x)`：生成0到x之间的随机数

二元函数:

- `max`, `min`, `atan2`, `noise`：如名称所述
- `dst(x, y)`：计算`sqrt(x*x+y*y)`

所有三角函数都使用角度制。

## 说明

- **所有变量都是全局变量。** 函数参数只是给它们赋值的语法糖。这是因为要识别和保护原始指令中用到的变量会很复杂。
- 小写单词+一个整数这种形式的标识符可能是连接到处理器的建筑，小心使用。
- 对变量`_`的赋值会被忽略。
- **不支持逻辑短路。** 所有子表达式都会被计算。
- 不支持函数调用语句。作为替代，可以将其返回值赋值给`_`。
- 函数必须先定义，后使用，并且直到右大括号才算定义完成。这也意味着MindC不支持递归。
