from collections import OrderedDict

import pytest

from waterloo.types import (
    ArgsSection,
    ArgTypes,
    ReturnsSection,
    ReturnType,
    TypeAtom,
    TypeSignature,
)
from waterloo.utils import mypy_py2_annotation


@pytest.mark.parametrize('example,expected', [
    (
        TypeSignature(
            args=ArgTypes(
                name=ArgsSection.ARGS,
                args=OrderedDict([
                    ('key', TypeAtom('str', [])),
                    ('num_tokens', TypeAtom('int', [])),
                    ('timeout', TypeAtom('int', [])),
                    ('retry_interval',
                     TypeAtom('Optional', [TypeAtom('float', [])])),
                ])
            ),
            returns=ReturnType(
                name=ReturnsSection.RETURNS,
                type=TypeAtom('bool', []),
            ),
        ),
        "# type: (str, int, int, Optional[float]) -> bool"
    ),
    (
        TypeSignature(
            args=ArgTypes(
                name=ArgsSection.ARGS,
                args=OrderedDict([
                    ('key', TypeAtom('str', [])),
                    ('num_tokens', TypeAtom('int', [])),
                    ('timeout', TypeAtom('int', [])),
                    ('retry_interval',
                     TypeAtom('Optional', [TypeAtom('float', [])])),
                ])
            ),
            returns=ReturnType(
                name=ReturnsSection.RETURNS,
                type=TypeAtom("Tuple", [
                    TypeAtom("int", []),
                    TypeAtom("str", []),
                    TypeAtom("ClassName", []),
                ])
            ),
        ),
        "# type: (str, int, int, Optional[float]) -> Tuple[int, str, ClassName]"
    )
])
def test_mypy_py2_annotation(example, expected):
    val = mypy_py2_annotation(example)
    assert val == expected
