from abc import abstractproperty
from dataclasses import dataclass
from pathlib import Path
from struct import pack, Struct
import sys
from typing import Literal, Any, Callable

ConstantIndex = int

class Constant:
    @abstractproperty
    def b(self) -> bytes:
        pass

class ClassInfo(Constant):
    def __init__(self, name: ConstantIndex):
        self.name = name
    @property
    def b(self) -> bytes:
        return b'\x07' + pack('>H', self.name)

class MemberRefInfo(Constant):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        self.class_i = class_i
        self.nametype_i = nametype_i
    @property
    def b(self) -> bytes:
        return self.tag + pack('>HH', self.class_i, self.nametype_i)

class FieldRefInfo(MemberRefInfo):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        super().__init__(class_i, nametype_i)
        self.tag = b'\x09'

class MethodRefInfo(MemberRefInfo):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        super().__init__(class_i, nametype_i)
        self.tag = b'\x0a'

class InterfaceMethodRefInfo(MemberRefInfo):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        super().__init__(class_i, nametype_i)
        self.tag = b'\x0b'

class StringInfo(Constant):
    def __init__(self, string_i: ConstantIndex) -> None:
        self.string_i = string_i
    @property
    def b(self) -> bytes:
        return b'\x08' + pack('>H', self.string_i)
    
class IntegerInfo(Constant):
    def __init__(self, value: int) -> None:
        self.value = value
    @property
    def b(self) -> bytes:
        return b'\x03' + pack('>i', self.value)

class FloatInfo(Constant):
    def __init__(self, value: float) -> None:
        self.value = value
    @property
    def b(self) -> bytes:
        return b'\x04' + pack('>f', self.value)

class LongInfo(Constant):
    entries = 2
    def __init__(self, value: int) -> None:
        self.value = value
    @property
    def b(self) -> bytes:
        return b'\x05' + pack('>q', self.value)

class DoubleInfo(Constant):
    entries = 2
    def __init__(self, value: float) -> None:
        self.value = value
    @property
    def b(self) -> bytes:
        return b'\x06' + pack('>d', self.value)

class NameAndTypeInfo(Constant):
    def __init__(self, name_i: ConstantIndex, descriptor_i: ConstantIndex) -> None:
        self.name_i = name_i
        self.descriptor_i = descriptor_i
    @property
    def b(self) -> bytes:
        return b'\x0c' + pack('>HH', self.name_i, self.descriptor_i)

class Utf8Info(Constant):
    def __init__(self, value: str) -> None:
        # TODO: real encoding
        assert '\0' not in value
        self.value = value.encode('ascii')
    @property
    def b(self) -> bytes:
        return b'\x01' + pack('>H', len(self.value)) + self.value

class MethodTypeInfo(Constant):
    def __init__(self, type_str: ConstantIndex) -> None:
        self.type_str = type_str
    @property
    def b(self) -> bytes:
        return b'\x10' + pack('>H', self.type_str)

# TODO FieldInfo

class Field:
    def __init__(self, s: str) -> None:
        self.s = s
    
    @classmethod
    def from_class(cls, class_name: str):
        return cls('L'+class_name+';')
    
    @classmethod
    def array(cls, member: "Field"):
        return cls('['+member.s)
        

FBYTE=Field('B')
FCHAR=Field('C')
FDOUBLE=Field('D')
FFLOAT=Field('F')
FINT=Field('I')
FLONG=Field('J')
FSHORT=Field('S')
FBOOL=Field('Z')
FVOID=Field('V')


@dataclass
class Method:
    result: Field
    params: list[Field]
    @property
    def s(self):
        return f'({"".join(p.s for p in self.params)}){self.result.s}'

@dataclass
class Attribute:
    name_idx: ConstantIndex
    info: bytes
    @property
    def b(self):
        return pack('>HI', self.name_idx, len(self.info)) + self.info

class CodeAttribute(Attribute):
    def __init__(self, max_stack: int, max_locals: int, code: bytes, name_idx: ConstantIndex) -> None:
        super().__init__(name_idx, pack('>HHI', max_stack, max_locals, len(code)) + code + pack('>HH',0,0))
        self.max_stack = max_stack
        self.max_locals = max_locals
        self.code = code

@dataclass
class MethodInfo:
    ACCESS_FLAGS = 0x1009 # public, synthetic, static
    name_idx: ConstantIndex
    descriptor_idx: ConstantIndex
    attributes: list[Attribute]
    @property
    def b(self) -> bytes:
        return pack('>HHHH', self.ACCESS_FLAGS, self.name_idx, self.descriptor_idx, len(self.attributes)) + b''.join(a.b for a in self.attributes)

@dataclass
class ClassFile:
    """
    A java .class file, using a set bytecode version
    """
    MAGIC = 0xCAFEBABE
    MINOR_VERSION = 0x0001
    MAJOR_VERSION = 52
    constants: list[Constant]
    ACCESS_FLAGS = 0x1001 # public
    this_class: ConstantIndex
    super_class: ConstantIndex
    interfaces: list[ConstantIndex]
#    fields: list[Field]
    methods: list[MethodInfo]
    attributes: list[Attribute]

    @property
    def b(self) -> bytes:
        return (
            pack('>IHHH', self.MAGIC, self.MINOR_VERSION, self.MAJOR_VERSION, len(self.constants)+1)
            + b''.join(c.b for c in self.constants)
            + pack('>HHHH', self.ACCESS_FLAGS, self.this_class, self.super_class, len(self.interfaces))
            + b''.join(pack('>H', i) for i in self.interfaces)
            + b'\x00\x00' # field count - TODO
            + pack('>H', len(self.methods))
            + b''.join(m.b for m in self.methods)
            + pack('>H', len(self.attributes))
            + b''.join(a.b for a in self.attributes)
        )

class ConstBuilder:
    def __init__(self) -> None:
        self.constants = []
    def add_constant(self, constant: Constant) -> ConstantIndex:
        self.constants.append(constant)
        return len(self.constants)
    def add_string(self, s: str) -> ConstantIndex:
        return self.add_constant(Utf8Info(s))
    def add_class(self, class_name: str) -> ConstantIndex:
        return self.add_constant(ClassInfo(self.add_constant(Utf8Info(class_name))))

const_builder = ConstBuilder()
code_s = const_builder.add_string('Code')
main_s = const_builder.add_string('main')
my_class_cls = const_builder.add_class('MyClass')
printstream_cls = const_builder.add_class('java/io/PrintStream')
object_cls = const_builder.add_class('java/lang/Object')
system_cls = const_builder.add_class('java/lang/System')
main_desc = const_builder.add_string('([Ljava/lang/String;)V')
hello_world_s = const_builder.add_string(sys.argv[1])
hello_world_const = const_builder.add_constant(StringInfo(hello_world_s))
out_field = const_builder.add_constant(
    FieldRefInfo(
        system_cls,
        const_builder.add_constant(
            NameAndTypeInfo(
                const_builder.add_string('out'), const_builder.add_string('Ljava/io/PrintStream;')
            )
        )
    )
)

println_method = const_builder.add_constant(
    MethodRefInfo(
        printstream_cls,
        const_builder.add_constant(
            NameAndTypeInfo(
                const_builder.add_string('println'),
                const_builder.add_string('(Ljava/lang/String;)V')
            )
        )
    )
)

my_class = ClassFile(
    constants=const_builder.constants,
    this_class=my_class_cls,
    super_class=object_cls,
    interfaces=[],
    methods=[MethodInfo(
        name_idx=main_s,
        descriptor_idx=main_desc,
        attributes=[
            CodeAttribute(
                max_stack=2,
                max_locals=1,
                code=(
                    b'\xb2'+pack('>H', out_field)
                    + b'\x12'+pack('>B', hello_world_const)
                    + b'\xb6'+pack('>H', println_method)+b'\xb1'
                    ),
                name_idx=code_s,
            )
        ]
    )],
    attributes=[]
)
Path('MyClass.class').write_bytes(my_class.b)