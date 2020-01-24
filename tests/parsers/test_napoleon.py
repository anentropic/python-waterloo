import re

from hypothesis import assume, given, strategies as st
import parsy
import pytest

from waterloo.parsers.napoleon import (
    args_head,
    arg_type,
    docstring_parser,
    dotted_var_path,
    ignored_line,
    p_arg_list,
    p_returns_block,
    rest_of_line,
    var_name,
    type_def,
)
from waterloo.types import TypeAtom


st_whitespace_char = st.text(' \t', min_size=1, max_size=1)


@st.composite
def st_whitespace(draw):
    """
    homogenous whitespace of random type (space or tab) and random length
    (including zero, i.e. '')
    """
    n = draw(st.integers(min_value=0, max_value=10))
    ws = draw(st_whitespace_char)
    return ws * n


@st.composite
def st_non_whitespace(draw, *args, **kwargs):
    """
    Drawn from (by default) the full range of Hypothesis' `text` strategy
    but eliminating whitespace chars (including \n)
    """
    val = draw(st.text(*args, **kwargs))
    assume(val.strip() == val)
    return val


st_optional_newline = st.one_of(
    st.just(''),
    st.just('\n'),
)


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
    name=st_non_whitespace(min_size=0, max_size=10),
    trailing_ws=st_whitespace(),
    newline=st.one_of(st.just(''), st.just('\n')),
)
def test_var_name(splat, name, trailing_ws, newline):
    """
    A var name begins with 0, 1 or 2 'splat' chars ("*")
    followed by a python var identifier
    optionally followed by non-newline whitespace
    not followed by a newline
    """
    example = f"{splat}{name}{trailing_ws}{newline}"
    if len(splat) <= 2 and name.isidentifier() and not newline:
        result = var_name.parse(example)
        assert result == f"{splat}{name}"
    else:
        with pytest.raises(parsy.ParseError):
            var_name.parse(example)


@given(
    segments=st.lists(st.text(min_size=0, max_size=10), min_size=1),
    trailing_ws=st_whitespace(),
    newline=st.one_of(st.just(''), st.just('\n')),
)
def test_dotted_var_path(segments, trailing_ws, newline):
    """
    A dotted var path is a '.'-separated list of python identifiers
    optionally followed by non-newline whitespace
    not followed by a newline
    """
    path = '.'.join(segments)
    example = f"{path}{trailing_ws}{newline}"
    if all(seg.isidentifier() for seg in segments) and not newline:
        result = dotted_var_path.parse(example)
        assert result == path
    else:
        with pytest.raises(parsy.ParseError):
            dotted_var_path.parse(example)


st_python_identifier = (
    st.from_regex(r'[^\W0-9][\w]*', fullmatch=True).filter(lambda s: s.isidentifier())
)


@st.composite
def st_dotted_var_path(draw):
    segments = draw(st.lists(st_python_identifier, min_size=1))
    return '.'.join(segments)


@st.composite
def st_noargs_typevar(draw):
    return TypeAtom(
        name=draw(st_dotted_var_path()),
        args=(),
    )


@st.composite
def st_generic_typevar(draw, st_children):
    """
    A type var with params (i.e. is 'generic'), without being one of the
    special cases such as homogenous tuple, callable (others?)

    Args:
        draw: provided by @st.composite
        st_children: another hypothesis strategy to draw from
            (first arg to function returned by decorator)
    """
    return TypeAtom(
        name=draw(st_dotted_var_path()),
        args=draw(st.lists(st_children))
    )


@st.composite
def st_homogenous_tuple_typevar(draw, st_children):
    return TypeAtom(
        name='Tuple',
        args=(draw(st_children), '...')
    )


@st.composite
def st_callable_typevar(draw, st_children):
    args_param = draw(st.lists(st_children, min_size=1))
    returns_param = draw(st_children)
    return TypeAtom(
        name='Callable',
        args=(args_param, returns_param)
    )


@st.composite
def st_type_atom(draw):
    example = draw(
        st.recursive(
            st_noargs_typevar(),
            lambda st_children: st.one_of(
                st_children,
                st_generic_typevar(st_children),
                st_homogenous_tuple_typevar(st_children),
                st_callable_typevar(st_children),
            ),
            max_leaves=5,
        )
    )
    return example


def _add_arbitrary_whitespace(segment, whitespace, newline):
    """
    Adds arbitrary whitespace and optional newlines
    """
    if segment.startswith('['):
        return f'{segment}{newline}{whitespace}'
    elif segment.startswith(','):
        return f'{segment}{newline}{whitespace}'
    elif segment.startswith(']'):
        return f'{newline}{whitespace}{segment}'
    else:
        return segment


@st.composite
def st_napoleon_type_annotation(draw):
    """
    Generate a type annotation that you might find in a napoleon docstring
    made from a valid TypeAtom but with arbitrary whitespace in valid locations

    - after a `[`
    - after a `,`
    - before a `]`
    """
    type_atom = draw(st_type_atom())
    annotation = type_atom.to_annotation()
    return ''.join(
        _add_arbitrary_whitespace(
            segment=segment.strip(),
            whitespace=draw(st_whitespace()),
            newline=draw(st_optional_newline),
        )
        for segment in re.split(r'([\[\]\,])', annotation)
    )


def _add_normalised_whitespace(segment):
    if segment.startswith(','):
        return f'{segment} '
    else:
        return segment


def _normalise_annotation(annotation):
    """
    Take a dirty annotation and strip spurious newlines and whitespace so that
    it should match the output from an equivalent TypeAtom.to_annotation()
    """
    return ''.join(
        _add_normalised_whitespace(segment.strip())
        for segment in re.split(r'([\[\]\,])', annotation)
    )


@given(st_napoleon_type_annotation())
def test_type_def(example):
    """
    Generate an arbitrary type annotation and check that we can round-trip
    compare it with the parsed result.
    """
    result = type_def.parse(example)
    normalised = _normalise_annotation(example)
    if isinstance(result, TypeAtom):
        result = result.to_annotation()
    assert normalised == result


@pytest.mark.parametrize('example', [
    "key (str): identifying a specific token bucket",
    "key (str): identifying a specific blah blah looks like (type):",
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
