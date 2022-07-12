import abc
from struct import pack

ConstantIndex = int

class Constant(abc.ABC):
    entries = 1
    @abc.abstractproperty
    def b(self) -> bytes:
        pass


class ClassInfo(Constant):
    def __init__(self, name: ConstantIndex):
        self.name = name

    @property
    def b(self) -> bytes:
        return b"\x07" + pack(">H", self.name)


class MemberRefInfo(Constant):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        self.class_i = class_i
        self.nametype_i = nametype_i

    @property
    def b(self) -> bytes:
        return self.tag + pack(">HH", self.class_i, self.nametype_i)


class FieldRefInfo(MemberRefInfo):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        super().__init__(class_i, nametype_i)
        self.tag = b"\x09"


class MethodRefInfo(MemberRefInfo):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        super().__init__(class_i, nametype_i)
        self.tag = b"\x0a"


class InterfaceMethodRefInfo(MemberRefInfo):
    def __init__(self, class_i: ConstantIndex, nametype_i: ConstantIndex) -> None:
        super().__init__(class_i, nametype_i)
        self.tag = b"\x0b"


class StringInfo(Constant):
    def __init__(self, string_i: ConstantIndex) -> None:
        self.string_i = string_i

    @property
    def b(self) -> bytes:
        return b"\x08" + pack(">H", self.string_i)


class IntegerInfo(Constant):
    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def b(self) -> bytes:
        return b"\x03" + pack(">i", self.value)


class FloatInfo(Constant):
    def __init__(self, value: float) -> None:
        self.value = value

    @property
    def b(self) -> bytes:
        return b"\x04" + pack(">f", self.value)


class LongInfo(Constant):
    entries = 2

    def __init__(self, value: int) -> None:
        self.value = value

    @property
    def b(self) -> bytes:
        return b"\x05" + pack(">q", self.value)


class DoubleInfo(Constant):
    entries = 2

    def __init__(self, value: float) -> None:
        self.value = value

    @property
    def b(self) -> bytes:
        return b"\x06" + pack(">d", self.value)


class NameAndTypeInfo(Constant):
    def __init__(self, name_i: ConstantIndex, descriptor_i: ConstantIndex) -> None:
        self.name_i = name_i
        self.descriptor_i = descriptor_i

    @property
    def b(self) -> bytes:
        return b"\x0c" + pack(">HH", self.name_i, self.descriptor_i)


class Utf8Info(Constant):
    def __init__(self, value: str) -> None:
        # TODO: real encoding
        assert "\0" not in value
        self.value = value.encode("ascii")

    @property
    def b(self) -> bytes:
        return b"\x01" + pack(">H", len(self.value)) + self.value


class MethodTypeInfo(Constant):
    def __init__(self, type_str: ConstantIndex) -> None:
        self.type_str = type_str

    @property
    def b(self) -> bytes:
        return b"\x10" + pack(">H", self.type_str)


class ConstBuilder:
    def __init__(self) -> None:
        self.constants = []
        self.idx = 1

    def add_constant(self, constant: Constant) -> ConstantIndex:
        self.constants.append(constant)
        self.idx += constant.entries
        return self.idx - constant.entries

    def add_string(self, s: str) -> ConstantIndex:
        return self.add_constant(Utf8Info(s))

    def add_class(self, class_name: str) -> ConstantIndex:
        return self.add_constant(ClassInfo(self.add_constant(Utf8Info(class_name))))
