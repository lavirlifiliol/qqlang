from dataclasses import dataclass
from struct import pack
from constant import ConstantIndex, ConstPool


@dataclass
class Attribute:
    name_idx: ConstantIndex
    info: bytes

    @property
    def b(self):
        return pack(">HI", self.name_idx, len(self.info)) + self.info


class CodeAttribute(Attribute):
    def __init__(
        self, max_stack: int, max_locals: int, code: bytes, name_idx: ConstantIndex
    ) -> None:
        super().__init__(
            name_idx,
            pack(">HHI", max_stack, max_locals, len(code)) + code + pack(">HH", 0, 0),
        )
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.code = code


@dataclass
class MethodInfo:
    ACCESS_FLAGS = 0x1009  # public, synthetic, static
    name_idx: ConstantIndex
    descriptor_idx: ConstantIndex
    attributes: list[Attribute]

    @property
    def b(self) -> bytes:
        return (
            pack(
                ">HHHH",
                self.ACCESS_FLAGS,
                self.name_idx,
                self.descriptor_idx,
                len(self.attributes),
            )
            + b"".join(a.b for a in self.attributes)
        )


# TODO FieldInfo


@dataclass
class ClassFile:
    """
    A java .class file, using a set bytecode version
    """

    MAGIC = 0xCAFEBABE
    MINOR_VERSION = 0x0001
    MAJOR_VERSION = 52
    constants: ConstPool
    ACCESS_FLAGS = 0x1001  # public
    this_class: ConstantIndex
    super_class: ConstantIndex
    interfaces: list[ConstantIndex]
    #    fields: list[Field]
    methods: list[MethodInfo]
    attributes: list[Attribute]

    @property
    def b(self) -> bytes:
        return (
            pack(
                ">IHHH",
                self.MAGIC,
                self.MINOR_VERSION,
                self.MAJOR_VERSION,
                len(self.constants) + 1,
            )
            + b"".join(c.b for c in self.constants)
            + pack(
                ">HHHH",
                self.ACCESS_FLAGS,
                self.this_class,
                self.super_class,
                len(self.interfaces),
            )
            + b"".join(pack(">H", i) for i in self.interfaces)
            + b"\x00\x00"  # field count - TODO
            + pack(">H", len(self.methods))
            + b"".join(m.b for m in self.methods)
            + pack(">H", len(self.attributes))
            + b"".join(a.b for a in self.attributes)
        )
