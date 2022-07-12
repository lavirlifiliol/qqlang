import sys
from struct import pack
from pathlib import Path
from constant import (
    ConstPool,
    MethodRefInfo,
    NameAndTypeInfo,
    StringInfo,
    FieldRefInfo,
)
from class_file import ClassFile, MethodInfo, CodeAttribute

if __name__ != "__main__":
    raise ImportError("This file is not intended to be imported")

pool = ConstPool()

my_class = ClassFile(
    constants=pool,
    this_class=pool.class_["MyClass"],
    super_class=pool.class_["java/lang/Object"],
    interfaces=[],
    methods=[
        MethodInfo(
            name_idx=pool.utf["main"],
            descriptor_idx=pool.utf["([Ljava/lang/String;)V"],
            attributes=[
                CodeAttribute(
                    max_stack=2,
                    max_locals=1,
                    code=(
                        b"\xb2"
                        + pack(">H", pool.field_ref["java/lang/System", "out", "Ljava/io/PrintStream;"])
                        + b"\x12"
                        + pack(">B", pool.str[sys.argv[1]])
                        + b"\xb6"
                        + pack(">H", pool.method_ref["java/io/PrintStream", "println", "(Ljava/lang/String;)V"])
                        + b"\xb1"
                    ),
                    name_idx=pool.utf['Code'],
                )
            ],
        )
    ],
    attributes=[],
)
Path("MyClass.class").write_bytes(my_class.b)
