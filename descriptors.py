from dataclasses import dataclass


class Field:
    def __init__(self, s: str) -> None:
        self.s = s

    @classmethod
    def from_class(cls, class_name: str):
        return cls("L" + class_name + ";")

    @classmethod
    def array(cls, member: "Field"):
        return cls("[" + member.s)


FBYTE = Field("B")
FCHAR = Field("C")
FDOUBLE = Field("D")
FFLOAT = Field("F")
FINT = Field("I")
FLONG = Field("J")
FSHORT = Field("S")
FBOOL = Field("Z")
FVOID = Field("V")


@dataclass
class Method:
    result: Field
    params: list[Field]

    @property
    def s(self):
        return f'({"".join(p.s for p in self.params)}){self.result.s}'
