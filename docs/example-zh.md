# 示例程序

下面是一段可以正常编译并有实际功能的程序。

```
def print_num(n) {
    if (n < 10) $ print 0
    $ print n
}

def print_colon() {
    if (show_colon) {
        $ print ":"
    } else {
        $ print " "
    }
}

def print_time(hour, minute, second) {
    _ = print_num(hour)
    _ = print_colon()
    _ = print_num(minute)
    _ = print_colon()
    _ = print_num(second)
    $ printflush message1
}

time = @time // 1000
show_colon = (@time % 1000 < 500)
_ = print_time(time // 3600 % 24, time // 60 % 60, time % 60)
```

这段程序首先定义了两个辅助函数，第一个输出两位整数，第二个根据全局标志选择输出冒号或空格。然后定义第三个函数，利用前两个函数输出一组时间。主过程中，利用内置变量`@time`计算时间的三个分量，最后调用之前定义的函数完成输出。

编译这段程序，将编译结果导入到Mindustry的处理器中，就可以在信息板上看到当前时间（UTC）。如下图所示。

![](../assets/example-ingame.png)
