import parsy
import pytest

from waterloo.parsers.napoleon import (
    args_head,
    arg_type,
    docstring_parser,
    ignored_line,
    p_arg_list,
    p_returns_block,
    rest_of_line,
    var_name,
    type_def,
)


def test_args_head():
    # TODO permutations of leading whitespace and Kwargs etc
    example = """Args:
"""
    result = args_head.parse(example)
    assert result == 'Args'

    no_newline = """Args:"""
    with pytest.raises(parsy.ParseError):
        args_head.parse(no_newline)


@pytest.mark.parametrize('example', [
    "str",
    "Dict",
    "var_1_2_abc",
    "ClassName",
])
def test_var_name_valid(example):
    result = var_name.parse(example)
    assert result == example


@pytest.mark.parametrize('example', [
    "dotted.path",
    "1name",
    "no-hyphens",
    "one two three",
])
def test_var_name_invalid(example):
    with pytest.raises(parsy.ParseError):
        var_name.parse(example)


@pytest.mark.parametrize('example,expected', [
    ("str", "str"),
    ("Dict", "Dict"),
    ("Dict[int, str]", ("Dict", ["int", "str"])),
    ("Dict[int, db.models.User]", ("Dict", ["int", "db.models.User"])),
    ("my.generic.Container[int]", ("my.generic.Container", ["int"])),
    ("Tuple[int, ...]", ("Tuple", ["int", "..."])),
    ("Callable[[int, str], Dict[int, str]]", ("Callable", [["int", "str"], ("Dict", ["int", "str"])])),
    ("""Tuple[
            int,
            str,
            ClassName
        ]""", ("Tuple", ["int", "str", "ClassName"])),
    ("""Tuple[
            int,
            str,
            ClassName,
        ]""", ("Tuple", ["int", "str", "ClassName"])),
])
def test_type_def_valid(example, expected):
    result = type_def.parse(example)
    assert result == expected


@pytest.mark.parametrize('example', [
    "key (str): identifying a specific token bucket",
    "key (str): ",
    "key (str):",
    "key (str)",
])
def test_arg_type(example):
    parser = arg_type << rest_of_line
    result = parser.parse(example)
    assert result == {
        'arg': 'key',
        'type': 'str',
    }


@pytest.mark.parametrize('example', [
    "\n",
    "Builds JSON blob to be stored in the paypal_log column\n",
    "        Builds JSON blob to be stored in the paypal_log column\n",
    "of engine_purchasetransaction. The Args: don't start here.\n",
    "        of engine_purchasetransaction. The Args: don't start here.\n",
    "Args: aren't here either.\n",
    "        Args: aren't here either.\n",
])
def test_ignored_line(example):
    result = ignored_line.parse(example)
    assert result == ""


def test_ignored_lines():
    example = """
    Builds JSON blob to be stored in the paypal_log column
    of engine_purchasetransaction. The Args: don't start here.
    Args: aren't here either.

    Args:
        key (str): identifying a specific token bucket
"""
    parser = ignored_line.many()
    result, remainder = parser.parse_partial(example)
    assert result == [""] * 5
    assert remainder == """    Args:
        key (str): identifying a specific token bucket
"""


def test_p_arg_list():
    example = """
        Kwargs:
            key (str): identifying a specific token bucket
            num_tokens (int): will block without consuming any tokens until
                this amount are available to be consumed
            timeout (int): seconds to block for
            retry_interval (Optional[float]): how long to wait between polling
                for tokens to be available. `None` means use default interval
                which is equal to time needed to replenish `num_tokens`.
            *inner_args
            **inner_kwargs: passed to inner function
    """
    section = p_arg_list.parse(example)
    assert section['name'] == 'Args'  # normalised "Kwargs" -> "Args"
    assert section['items'] == [
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
        {
            'arg': '*inner_args',
            'type': None,
        },
        {
            'arg': '**inner_kwargs',
            'type': None,
        },
    ]


def test_p_returns_block():
    example = """
        Yields:
            Optional[float]: how long to wait between polling
                for tokens to be available. `None` means use default interval
                which is equal to time needed to replenish `num_tokens`.
    """
    section = p_returns_block.parse(example)
    assert section['name'] == 'Yields'  # either "Returns" or "Yields", distinction preserved
    assert section['items'] == [
        ('Optional', ['float']),
    ]


def test_docstring_parser():
    example = """
        Will block thread until `num_tokens` could be consumed from token bucket `key`.

        Args:
            key (str): identifying a specific token bucket
            num_tokens (int): will block without consuming any tokens until
                this amount are availabe to be consumed
            timeout (int): seconds to block for
            retry_interval (Optional[float]): how long to wait between polling
                for tokens to be available. `None` means use default interval
                which is equal to time needed to replenish `num_tokens`.

        Returns:
            bool: whether we got the requested tokens or not
                (False if timed out)
        """
    expected = {
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
    }

    result = docstring_parser.parse(example)
    assert result == expected


def test_docstring_parser2():
    example = """
        Will block thread until `num_tokens` could be consumed from token bucket `key`.

        Args:
            key (str): identifying a specific token bucket
            num_tokens (int): will block without consuming any tokens until
                this amount are availabe to be consumed
            timeout (int): seconds to block for
            retry_interval (Optional[float]): how long to wait between polling
                for tokens to be available. `None` means use default interval
                which is equal to time needed to replenish `num_tokens`.

        Returns:
            Tuple[
                int,
                str,
                ClassName,
            ]
        """
    expected = {
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
    }

    result = docstring_parser.parse(example)
    assert result == expected
