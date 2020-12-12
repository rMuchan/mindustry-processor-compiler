# Mindustry处理器编译器

本项目定义了一种可以编译到Mindustry处理器指令的语言。

[语言定义](docs/langdef-zh.md)

[示例程序](docs/example-zh.md)

## 用法

本项目依赖Python 3。入口点是`mindc.py`，接受恰好一个参数，指定源文件。例如，编译`source.txt`中存储的程序，可以在命令行中运行下面的命令：

Windows上：

```
python mindc.py source.txt
```

Linux或MacOS上：

```
python3 mindc.py source.txt
```

如果源文件指定为`-`，编译器会从标准输入读取程序。

编译结果会被输出到标准输出上。没有参数指定输出文件，不过可以很容易地将输出重定向到文件。

## 贡献

这个编译器还没有经过充分的测试。如果你发现了错误，可以提交issue或者PR。
