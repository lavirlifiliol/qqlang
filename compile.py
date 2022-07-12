import sys
from struct import pack
from pathlib import Path
from constant import (
    ConstBuilder,
    MethodRefInfo,
    NameAndTypeInfo,
    StringInfo,
    FieldRefInfo,
)
from class_file import ClassFile, MethodInfo, CodeAttribute

if __name__ != "__main__":
    raise ImportError("This file is not intended to be imported")

const_builder = ConstBuilder()
code_s = const_builder.add_string("Code")
main_s = const_builder.add_string("main")
my_class_cls = const_builder.add_class("MyClass")
printstream_cls = const_builder.add_class("java/io/PrintStream")
object_cls = const_builder.add_class("java/lang/Object")
system_cls = const_builder.add_class("java/lang/System")
main_desc = const_builder.add_string("([Ljava/lang/String;)V")
hello_world_s = const_builder.add_string(sys.argv[1])
hello_world_const = const_builder.add_constant(StringInfo(hello_world_s))
out_field = const_builder.add_constant(
    FieldRefInfo(
        system_cls,
        const_builder.add_constant(
            NameAndTypeInfo(
                const_builder.add_string("out"),
                const_builder.add_string("Ljava/io/PrintStream;"),
            )
        ),
    )
)

println_method = const_builder.add_constant(
    MethodRefInfo(
        printstream_cls,
        const_builder.add_constant(
            NameAndTypeInfo(
                const_builder.add_string("println"),
                const_builder.add_string("(Ljava/lang/String;)V"),
            )
        ),
    )
)

my_class = ClassFile(
    constants=const_builder.constants,
    this_class=my_class_cls,
    super_class=object_cls,
    interfaces=[],
    methods=[
        MethodInfo(
            name_idx=main_s,
            descriptor_idx=main_desc,
            attributes=[
                CodeAttribute(
                    max_stack=2,
                    max_locals=1,
                    code=(
                        b"\xb2"
                        + pack(">H", out_field)
                        + b"\x12"
                        + pack(">B", hello_world_const)
                        + b"\xb6"
                        + pack(">H", println_method)
                        + b"\xb1"
                    ),
                    name_idx=code_s,
                )
            ],
        )
    ],
    attributes=[],
)
Path("MyClass.class").write_bytes(my_class.b)
