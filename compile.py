import sys
from io import TextIOBase
from pathlib import Path
from constant import ConstPool
from class_file import ClassFile, MethodInfo, CodeAttribute
from typing import Any
import codegen as c
from enum import Enum


class Type(Enum):
    VOID = 0
    STRING = 1
    LONG = 2


if __name__ != "__main__":
    raise ImportError("This file is not intended to be imported")


class Compiler:
    special_chars = '()"'

    def __init__(self, stream: TextIOBase) -> None:
        self.pool = ConstPool()
        self._stack = 1
        self.max_stack = 1
        self.current_locals = 1
        self.insns = []
        self.stream = stream
        self.current_char = None
        self.current_fn = None
        self.col = 0
        self.row = 1
        self.line = ""

    def advance(self) -> str:
        self.current_char = self.stream.read(1)
        if self.current_char == "\n":
            self.line = ""
            self.row += 1
            self.col = 0
        else:
            self.col += 1
            self.line += self.current_char
        if not self.current_char:
            raise EOFError()
        return self.current_char

    def advance_value(self) -> str:
        while self.current_char.isspace():
            self.advance()
        return self.current_char

    def read_atom(self) -> str:
        text = ""
        while (
            not self.current_char.isspace()
            and self.current_char not in self.special_chars
        ):
            text += self.current_char
            self.advance()
        if not text:
            raise SyntaxError("Empty sexpr not allowed")
        return text

    def compile_atom(self, atom: str) -> Type:
        try:
            v = int(atom)
        except ValueError:
            if atom.startswith('"'):
                self.add_insn(1, c.Ldc(self.pool.str[atom[1:]]))
                return Type.STRING
            else:
                raise SyntaxError("use of non-numeric value")
        self.add_insn(2, c.Ldc2(self.pool.long[v]))
        return Type.LONG

    @property
    def stack(self):
        return self._stack

    @stack.setter
    def stack(self, v):
        self._stack = v
        self.max_stack = max(self.max_stack, v)

    def add_insn(self, stack_d: int, insn: c.Insn):
        self.insns.append(insn)
        self.stack += stack_d

    def compile_fn_start(self, atom: str) -> object:
        match atom:
            case "+":
                return 0
            case "print":
                self.add_insn(
                    1,
                    c.GetStatic(
                        self.pool.field_ref[
                            "java/lang/System", "out", "Ljava/io/PrintStream;"
                        ]
                    ),
                )
            case _:
                raise SyntaxError(f"Unknown function {atom!r}")

    def compile_sexpr_type(self, t: Type) -> None:
        if self.compile_sexpr() is not t:
            raise TypeError(f"Expected type {t!r}")

    def compile_sexpr_fn_arg(self, atom: str, user_data: object) -> object:
        match atom:
            case "+":
                assert isinstance(user_data, int)
                self.compile_sexpr_type(Type.LONG)
                return user_data + 1
            case "print":
                assert user_data is None
                self.add_insn(1, c.Dup())
                atype = self.compile_sexpr()
                if atype is Type.LONG:
                    self.add_insn(
                        -3,
                        c.InvokeVirtual(
                            self.pool.method_ref["java/io/PrintStream", "print", "(J)V"]
                        ),
                    )
                elif atype is Type.STRING:
                    self.add_insn(
                        -2,
                        c.InvokeVirtual(
                            self.pool.method_ref[
                                "java/io/PrintStream", "print", "(Ljava/lang/String;)V"
                            ]
                        ),
                    )
                else:
                    raise TypeError(f"cannot print {atype!r}")
            case _:
                raise SyntaxError("Unknown function")

    def compile_fn_end(self, atom: str, user_data: object) -> Type:
        match atom:
            case "+":
                assert isinstance(user_data, int)
                if user_data == 0:
                    self.add_insn(2, c.Ldc2(self.pool.long[0]))
                for _ in range(user_data - 1):
                    self.add_insn(-2, c.LAdd())
                return Type.LONG
            case "print":
                self.add_insn(1, c.Dup())
                self.add_insn(
                    -1,
                    c.InvokeVirtual(
                        self.pool.method_ref["java/io/PrintStream", "println", "()V"]
                    ),
                )
                return Type.VOID
            case _:
                raise SyntaxError("Unknown function")

    def read_str(self) -> str:
        text = '"'
        while self.current_char != '"' and self.current_char != "\n":
            text += self.current_char
            self.advance()
        if self.current_char == "\n":
            raise SyntaxError("Unclosed string")
        self.advance()
        return text

    def compile_sexpr(self) -> Type:
        if self.current_char == "(":
            self.advance()
            self.advance_value()
            try:
                fn = self.read_atom()
                data = self.compile_fn_start(fn)
                while self.advance_value() != ")":
                    data = self.compile_sexpr_fn_arg(fn, data)
                ret = self.compile_fn_end(fn, data)
                self.advance()  # skip the )
                return ret
            except EOFError:
                raise SyntaxError("Unclosed sexpr")
        elif self.current_char == '"':
            self.advance()
            return self.compile_atom(self.read_str())
        else:
            atom = self.read_atom()
            return self.compile_atom(atom)

    def compile(self) -> None:
        try:
            self.advance()
            self.advance_value()
            while True:
                self.compile_sexpr()
                self.advance_value()
        except EOFError:
            self.add_insn(0, c.Return())
        except SyntaxError as e:
            self.line += self.stream.readline()
            print(f"{self.row}:{self.col}: {e}\n{self.line}{'^':>{self.col}}\n")
            raise SystemExit(1)


compiler = Compiler(sys.stdin)
compiler.compile()

pool = compiler.pool

code = CodeAttribute(
    max_stack=compiler.max_stack,
    max_locals=1,
    code=c.code(*compiler.insns),
    name_idx=pool.utf["Code"],
)

my_class = ClassFile(
    constants=pool,
    this_class=pool.class_["MyClass"],
    super_class=pool.class_["java/lang/Object"],
    interfaces=[],
    methods=[
        MethodInfo(
            name_idx=pool.utf["main"],
            descriptor_idx=pool.utf["([Ljava/lang/String;)V"],
            attributes=[code],
        )
    ],
    attributes=[],
)
Path("MyClass.class").write_bytes(my_class.b)
