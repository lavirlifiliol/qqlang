import abc
from struct import pack
from constant import ConstantIndex


class Insn(abc.ABC):
    @abc.abstractproperty
    def b(self) -> bytes:
        pass


class Ldc(Insn):
    def __init__(self, c: ConstantIndex) -> None:
        self.c = c

    @property
    def b(self) -> bytes:
        if self.c < 256:
            return b"\x12" + pack(">B", self.c)
        else:
            return b"\x13" + pack(">H", self.c)


class GetStatic(Insn):
    def __init__(self, field_ref: ConstantIndex) -> None:
        self.fr = field_ref

    @property
    def b(self):
        return b"\xb2" + pack(">H", self.fr)


class GetField(Insn):
    def __init__(self, field_ref: ConstantIndex) -> None:
        self.fr = field_ref

    @property
    def b(self):
        return b"\xb4" + pack(">H", self.fr)


class InvokeStatic(Insn):
    def __init__(self, method_ref: ConstantIndex) -> None:
        self.mr = method_ref

    @property
    def b(self):
        return b"\xb8" + pack(">H", self.mr)


class InvokeVirtual(Insn):
    def __init__(self, method_ref: ConstantIndex) -> None:
        self.mr = method_ref

    @property
    def b(self):
        return b"\xb6" + pack(">H", self.mr)


class Return(Insn):
    @property
    def b(self) -> bytes:
        return b"\xb1"


def code(*args: Insn) -> bytes:
    return b"".join(arg.b for arg in args)
