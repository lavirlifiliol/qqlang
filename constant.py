import abc
from collections import UserDict
from collections.abc import Mapping
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


class DefaultDict(UserDict):
    def __init__(self, default_factory):
        super().__init__()
        self.default_factory = default_factory

    def __missing__(self, key):
        value = self.default_factory(key)
        self[key] = value
        return value


class ConstPool:
    def __init__(self) -> None:
        self.constants = []
        self.utf = DefaultDict(self._add_utf)
        self.str = DefaultDict(self._add_str)
        self.class_ = DefaultDict(self._add_class)
        self.nametype = DefaultDict(self._add_nametype)
        self.method_ref = DefaultDict(self._add_method_ref)
        self.field_ref = DefaultDict(self._add_field_ref)
        self.long = DefaultDict(self._add_long)
        self.idx = 1

    def __len__(self) -> int:
        return self.idx - self.constants[-1].entries

    def __iter__(self) -> int:
        yield from self.constants

    def _add_constant(self, constant: Constant) -> ConstantIndex:
        self.constants.append(constant)
        self.idx += constant.entries
        return self.idx - constant.entries

    def _add_long(self, value: int) -> ConstantIndex:
        return self._add_constant(LongInfo(value))

    def _add_utf(self, s: str) -> ConstantIndex:
        return self._add_constant(Utf8Info(s))

    def _add_str(self, s: str) -> ConstantIndex:
        return self._add_constant(StringInfo(self.utf[s]))

    def _add_class(self, class_name: str) -> ConstantIndex:
        return self._add_constant(ClassInfo(self.utf[class_name]))

    def _add_nametype(self, nametype: tuple[str, str]) -> ConstantIndex:
        return self._add_constant(
            NameAndTypeInfo(self.utf[nametype[0]], self.utf[nametype[1]])
        )

    def _add_method_ref(self, params: tuple[str, str, str]) -> ConstantIndex:
        return self._add_constant(
            MethodRefInfo(self.class_[params[0]], self.nametype[params[1], params[2]])
        )

    def _add_field_ref(self, params: tuple[str, str, str]) -> ConstantIndex:
        return self._add_constant(
            FieldRefInfo(self.class_[params[0]], self.nametype[params[1], params[2]])
        )
