from hypothesis import given, strategies as st
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


st_whitespace_char = st.text(' \t', min_size=1, max_size=1)


@st.composite
def st_whitespace(draw):
    """
    homogenous whitespace of random type and length (including '')
    """
    n = draw(st.integers(min_value=0, max_value=10))
    ws = draw(st_whitespace_char)
    return ws * n


VALID_ARGS_SECTION_NAMES = {'Args', 'Kwargs'}

st_valid_args_section_name = st.one_of(
    *(st.just(word) for word in VALID_ARGS_SECTION_NAMES)
)

st_invalid_args_section_name = st.text().filter(
    lambda t: t not in VALID_ARGS_SECTION_NAMES
)

VALID_ARGS_HEAD_TEMPLATE = "{section_name}:{trailing_whitespace}\n"

st_invalid_args_head_template = st.one_of(
    st.just("{section_name}:{trailing_whitespace}"),
    st.just("{section_name}{trailing_whitespace}\n"),
)


@st.composite
def st_valid_args_head(draw):
    section_name = draw(st_valid_args_section_name)
    trailing_whitespace = draw(st_whitespace())
    return VALID_ARGS_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def st_invalid_args_head_bad_name(draw):
    section_name = draw(st_invalid_args_section_name)
    trailing_whitespace = draw(st_whitespace())
    return VALID_ARGS_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def st_invalid_args_head_bad_template(draw):
    leading_whitespace = draw(st_whitespace())
    section_name = draw(st_valid_args_section_name)
    trailing_whitespace = draw(st_whitespace())
    template = draw(st_invalid_args_head_template)
    return template.format(
        leading_whitespace=leading_whitespace,
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@given(st_valid_args_head())
def test_valid_args_head(example):
    result = args_head.parse(example)
    assert result == "Args"  # (Section name has been normalised)


@given(st.one_of(
    st_invalid_args_head_bad_name(),
    st_invalid_args_head_bad_template(),
))
def test_invalid_args_head(example):
    with pytest.raises(parsy.ParseError):
        args_head.parse(example)


@given(
    splat=st.text('*', min_size=0, max_size=4),
    name=st.text(min_size=0, max_size=10),
    trailing_ws=st_whitespace(),
    newline=st.one_of(st.just(''), st.just('\n')),
)
def test_var_name(splat, name, trailing_ws, newline):
    example = f"{splat}{name}{trailing_ws}{newline}"
    if len(splat) <= 2 and name.isidentifier() and not newline:
        result = var_name.parse(example)
        assert result == f"{splat}{name}"
    else:
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
