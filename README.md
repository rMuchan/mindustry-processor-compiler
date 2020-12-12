# Mindustry Processor Compiler

[中文版README](README-zh.md)

This project defines a language that compiles to Mindustry processor instructions.

[Language Definition](docs/langdef.md)

[An Example](docs/example.md)

## Usage

This project requires python3. The entry point is `mindc.py`. It accepts exactly one argument, specifying the source file. For example, to compile a program stored in `source.txt`, run following commands from Terminal:

On Windows:

```
python mindc.py source.txt
```

On Linux or MacOS:

```
python3 mindc.py source.txt
```

If you specify `-` as source file, the source will be read from stdin.

Compiled code will be printed on stdout. There are no arguments for specifying output file, but it can be easily redirected.

## Contributing

This compiler is not well-tested yet. If you think something works wrongly, feel free to open an issue/PR.
