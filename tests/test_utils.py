import pytest

from waterloo.utils import type_atom_to_str, mypy_py2_annotation


@pytest.mark.parametrize('expected,example', [
    ("str", "str"),
    ("Dict", "Dict"),
    ("Dict[int, str]", ("Dict", ["int", "str"])),
    ("Dict[int, db.models.User]", ("Dict", ["int", "db.models.User"])),
    ("my.generic.Container[int]", ("my.generic.Container", ["int"])),
    ("Tuple[int, ...]", ("Tuple", ["int", "..."])),
    ("Callable[[int, str], Dict[int, str]]", ("Callable", [["int", "str"], ("Dict", ["int", "str"])])),
])
def test_type_atom_to_str(expected, example):
    val = type_atom_to_str(example)
    assert val == expected


@pytest.mark.parametrize('example,expected', [
    (
        {
            'args': {
                'name': 'Args',
                'items': [
                    {
                        'arg': 'key',
                        'type': 'str',
                    },
                    {
                        'arg': 'num_tokens',
                        'type': 'int',
                    },
                    {
                        'arg': 'timeout',
                        'type': 'int',
                    },
                    {
                        'arg': 'retry_interval',
                        'type': ('Optional', ['float']),
                    },
                ],
            },
            'returns': {
                'name': 'Returns',
                'items': [
                    'bool'
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
                        'type': 'str',
                    },
                    {
                        'arg': 'num_tokens',
                        'type': 'int',
                    },
                    {
                        'arg': 'timeout',
                        'type': 'int',
                    },
                    {
                        'arg': 'retry_interval',
                        'type': ('Optional', ['float']),
                    },
                ],
            },
            'returns': {
                'name': 'Returns',
                'items': [
                    ("Tuple", ["int", "str", "ClassName"])
                ],
            },
        },
        "# type: (str, int, int, Optional[float]) -> Tuple[int, str, ClassName]"
    )
])
def test_mypy_py2_annotation(example, expected):
    val = mypy_py2_annotation(example)
    assert val == expected
