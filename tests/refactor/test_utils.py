from collections import OrderedDict

import pytest

from waterloo.parsers.napoleon import docstring_parser
from waterloo.refactor.utils import find_local_types, get_type_comment, remove_types
from waterloo.types import (
    ArgsSection,
    ArgTypes,
    LocalTypes,
    ReturnsSection,
    ReturnType,
    TypeAtom,
    TypeSignature,
)


@pytest.mark.parametrize(
    "example,expected",
    [
        (
            TypeSignature.factory(
                arg_types=ArgTypes.factory(
                    name=ArgsSection.ARGS,
                    args=OrderedDict(
                        [
                            ("key", TypeAtom("str", [])),
                            ("num_tokens", TypeAtom("int", [])),
                            ("timeout", TypeAtom("int", [])),
                            (
                                "retry_interval",
                                TypeAtom("Optional", [TypeAtom("float", [])]),
                            ),
                        ]
                    ),
                ),
                return_type=ReturnType.factory(
                    name=ReturnsSection.RETURNS, type_def=TypeAtom("bool", []),
                ),
            ),
            "# type: (str, int, int, Optional[float]) -> bool",
        ),
        (
            TypeSignature.factory(
                arg_types=ArgTypes.factory(
                    name=ArgsSection.ARGS,
                    args=OrderedDict(
                        [
                            ("key", TypeAtom("str", [])),
                            ("num_tokens", TypeAtom("int", [])),
                            ("timeout", TypeAtom("int", [])),
                            (
                                "retry_interval",
                                TypeAtom("Optional", [TypeAtom("float", [])]),
                            ),
                        ]
                    ),
                ),
                return_type=ReturnType.factory(
                    name=ReturnsSection.RETURNS,
                    type_def=TypeAtom(
                        "Tuple",
                        [
                            TypeAtom("int", []),
                            TypeAtom("str", []),
                            TypeAtom("ClassName", []),
                        ],
                    ),
                ),
            ),
            "# type: (str, int, int, Optional[float]) -> Tuple[int, str, ClassName]",
        ),
        (
            TypeSignature.factory(
                arg_types=ArgTypes.factory(
                    name=ArgsSection.ARGS,
                    args=OrderedDict(
                        [
                            ("regular_arg", TypeAtom("str", [])),
                            ("*args", TypeAtom("int", [])),
                            ("**kwargs", TypeAtom("str", [])),
                        ]
                    ),
                ),
                return_type=None,
            ),
            "# type: (str, *int, **str) -> None",
        ),
    ],
)
def test_get_type_comment(example, expected):
    val = get_type_comment(example, name_to_strategy={})
    assert val == expected


@pytest.mark.parametrize(
    "example,expected",
    [
        (
            """Kwargs:
  A (A)
Return:
  A
""",
            "Kwargs:\n  A\n",
        ),
        (
            """Args:
  A (A): whatever
Return:
  B: whatever
""",
            """Args:
  A: whatever
Return:
  whatever
""",
        ),
        (
            """Args:
  A (A):
    whatever
Return:
  B:
    whatever
""",
            """Args:
  A:
    whatever
Return:
    whatever
""",
        ),
        ("""0""", "0"),
        (" Return:\n  A\n    \n", "    \n"),
        (" Return:\n  A\n\n", "\n"),
        ("Args:\n  A (A)\nReturn:\n  A\n      \n", "Args:\n  A\n      \n"),
        ("Return:\n  A\n0", "0"),
        ("\n\nReturn:\n  A\n", ""),
        (
            "\n Args:\n  A (A)\n Return:\n  A\n    0\n",
            "\n Args:\n  A\n Return:\n    0\n",
        ),
        ("\nReturn:\n  A\n", ""),
        ("\nReturn:\n  A\n      0\n", "\nReturn:\n      0\n"),
    ],
)
def test_remove_types(example, expected):
    signature = docstring_parser.parse(example)
    result = remove_types(example, signature)

    print(repr(result))
    assert result == expected


def test_find_local_types():
    expected = LocalTypes.factory(
        type_defs={"T", "TopLevel", "InnerClass"},
        star_imports={"serious"},
        names_to_packages={
            "Irrelevant": "..sub",
            "Nonsense": "..sub",
            "ReallyUnused": "..sub",
            "Product": "other.module",
            "Imported": "some.module",
            "ConditionallyImported": "some.module",
            "InnerImported": "some.module",
            "TypeVar": "typing",
            "Union": "typing",
        },
        package_imports={"logging", "nott.so.serious"},
    )

    result = find_local_types("tests/fixtures/napoleon.py")

    assert result == expected
