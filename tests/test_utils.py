import pytest

from waterloo.types import TypeAtom
from waterloo.utils import mypy_py2_annotation


@pytest.mark.parametrize('example,expected', [
    (
        {
            'args': {
                'name': 'Args',
                'items': [
                    {
                        'arg': 'key',
                        'type': TypeAtom('str', []),
                    },
                    {
                        'arg': 'num_tokens',
                        'type': TypeAtom('int', []),
                    },
                    {
                        'arg': 'timeout',
                        'type': TypeAtom('int', []),
                    },
                    {
                        'arg': 'retry_interval',
                        'type': TypeAtom('Optional', [TypeAtom('float', [])]),
                    },
                ],
            },
            'returns': {
                'name': 'Returns',
                'items': [
                    TypeAtom('bool', [])
                ],
            },
        },
        "# type: (str, int, int, Optional[float]) -> bool"
    ),
    (
        {
            'args': {
                'name': 'Args',
                'items': [
                    {
                        'arg': 'key',
                        'type': TypeAtom('str', []),
                    },
                    {
                        'arg': 'num_tokens',
                        'type': TypeAtom('int', []),
                    },
                    {
                        'arg': 'timeout',
                        'type': TypeAtom('int', []),
                    },
                    {
                        'arg': 'retry_interval',
                        'type': TypeAtom('Optional', [TypeAtom('float', [])]),
                    },
                ],
            },
            'returns': {
                'name': 'Returns',
                'items': [
                    TypeAtom("Tuple", [
                        TypeAtom("int", []),
                        TypeAtom("str", []),
                        TypeAtom("ClassName", []),
                    ])
                ],
            },
        },
        "# type: (str, int, int, Optional[float]) -> Tuple[int, str, ClassName]"
    )
])
def test_mypy_py2_annotation(example, expected):
    val = mypy_py2_annotation(example)
    assert val == expected
