# Example

Here shows an example of functional programs.

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

This program defines two utility functions. One prints a 2-digit number. The other prints a colon or a whitespace depending on a global flag. Then another function is defined, utilizing the previous ones to print a time. Main procedure calculates arguments from builtin variable `@time` and invokes the fore mentioned function.

Compile this program and import the output to a Mindustry processor, and the current time (in UTC) will be displayed on the linked message board, as shown in the following image.

![](../assets/example-ingame.png)
