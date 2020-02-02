import re
from collections import Counter
from functools import partial

import parsy
import pytest
from hypothesis import assume, given, note, strategies as st
from typing import Any, Dict, NamedTuple, Union

from waterloo.parsers.napoleon import (
    args_head,
    arg_type,
    docstring_parser,
    dotted_var_path,
    ignored_line,
    p_arg_list,
    p_returns_block,
    rest_of_line,
    returns_head,
    var_name,
    type_atom,
)
from waterloo.types import (
    TypeAtom,
    VALID_ARGS_SECTION_NAMES,
    VALID_RETURNS_SECTION_NAMES,
)


"""
Property-based test-cases for the parsers

These are more exhaustive than the handwritten tests (and found some bugs
and edge cases which they did not) but they are harder to understand.
They are also reassuringly slow to run ;)
"""


class Example(NamedTuple):
    example: Any
    context: Dict[str, Any]


st_whitespace_char = st.text(' \t', min_size=1, max_size=1)

st_small_lists = partial(st.lists, min_size=0, max_size=3)
st_small_lists_nonempty = partial(st.lists, min_size=1, max_size=4)


@st.composite
def st_whitespace(draw, min_size=0, max_size=10):
    """
    homogenous whitespace of random type (space or tab) and random length
    (including zero, i.e. '')
    """
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    ws = draw(st_whitespace_char)
    return ws * n


@st.composite
def st_strip_whitespace(draw, *args, **kwargs):
    """
    Drawn from (by default) the full range of Hypothesis' `text` strategy
    but eliminating initial/trailing whitespace chars, including \n, but
    not from middle of string.
    """
    kwargs['alphabet'] = st.characters(blacklist_characters="\n\r")
    val = draw(st.text(*args, **kwargs))
    assume(val.strip() == val)
    return val


st_optional_newline = st.one_of(
    st.just(''),
    st.just('\n'),
)


VALID_SECTION_HEAD_TEMPLATE = "{section_name}:{trailing_whitespace}\n"

st_invalid_section_head_template = st.one_of(
    st.just("{leading_whitespace}{section_name}:{trailing_whitespace}"),
    st.just("{leading_whitespace}{section_name}{trailing_whitespace}\n"),
)

st_valid_args_section_name = st.one_of(
    *(st.just(word) for word in VALID_ARGS_SECTION_NAMES)
)

st_invalid_args_section_name = st.text().filter(
    lambda t: t not in VALID_ARGS_SECTION_NAMES
)


@st.composite
def st_valid_args_head(draw):
    section_name = draw(st_valid_args_section_name)
    trailing_whitespace = draw(st_whitespace())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def st_invalid_args_head_bad_name(draw):
    section_name = draw(st_invalid_args_section_name)
    trailing_whitespace = draw(st_whitespace())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def st_invalid_args_head_bad_template(draw):
    leading_whitespace = draw(st_whitespace())
    section_name = draw(st_valid_args_section_name)
    trailing_whitespace = draw(st_whitespace())
    template = draw(st_invalid_section_head_template)
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


st_valid_returns_section_name = st.one_of(
    *(st.just(word) for word in VALID_RETURNS_SECTION_NAMES)
)

st_invalid_returns_section_name = st.text().filter(
    lambda t: t not in VALID_RETURNS_SECTION_NAMES
)


@st.composite
def st_valid_returns_head(draw):
    section_name = draw(st_valid_returns_section_name)
    trailing_whitespace = draw(st_whitespace())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def st_invalid_returns_head_bad_name(draw):
    section_name = draw(st_invalid_returns_section_name)
    trailing_whitespace = draw(st_whitespace())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def st_invalid_returns_head_bad_template(draw):
    leading_whitespace = draw(st_whitespace())
    section_name = draw(st_valid_returns_section_name)
    trailing_whitespace = draw(st_whitespace())
    template = draw(st_invalid_section_head_template)
    return template.format(
        leading_whitespace=leading_whitespace,
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@given(st_valid_returns_head())
def test_valid_returns_head(example):
    result = returns_head.parse(example)
    assert result in VALID_RETURNS_SECTION_NAMES
    normalised = VALID_RETURNS_SECTION_NAMES[result][1]
    assert result == normalised  # (Section name has been normalised)


@given(st.one_of(
    st_invalid_returns_head_bad_name(),
    st_invalid_returns_head_bad_template(),
))
def test_invalid_returns_head(example):
    with pytest.raises(parsy.ParseError):
        returns_head.parse(example)


@given(
    splat=st.text('*', min_size=0, max_size=4),
    name=st_strip_whitespace(min_size=0, max_size=10),
    trailing_ws=st_whitespace(),
    newline=st.one_of(st.just(''), st.just('\n')),
)
def test_arg_name(splat, name, trailing_ws, newline):
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
    segments=st_small_lists_nonempty(st.text(min_size=0, max_size=10)),
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
    st
    .from_regex(r'[^\W0-9][\w]*', fullmatch=True)
    .filter(lambda s: s.isidentifier())
)


@st.composite
def st_dotted_var_path(draw):
    segments = draw(st_small_lists_nonempty(st_python_identifier))
    return '.'.join(segments)


@st.composite
def st_noargs_typeatom(draw):
    return TypeAtom(
        name=draw(st_dotted_var_path()),
        args=(),
    )


@st.composite
def st_generic_typeatom(draw, st_children):
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
        args=draw(st_small_lists(st_children))
    )


@st.composite
def st_homogenous_tuple_typeatom(draw, st_children):
    return TypeAtom(
        name='Tuple',
        args=(draw(st_children), '...')
    )


@st.composite
def st_callable_typeatom(draw, st_children):
    args_param = draw(st_small_lists_nonempty(st_children))
    returns_param = draw(st_children)
    return TypeAtom(
        name='Callable',
        args=(args_param, returns_param)
    )


@st.composite
def st_type_atom(draw):
    """
    Generate arbitrarily nested TypeAtom instances
    """
    example = draw(
        st.recursive(
            st_noargs_typeatom(),
            lambda st_children: st.one_of(
                st_children,
                st_generic_typeatom(st_children),
                st_homogenous_tuple_typeatom(st_children),
                st_callable_typeatom(st_children),
            ),
            max_leaves=5,
        )
    )
    return example


def _add_arbitrary_whitespace(segment, whitespace, newline):
    """
    Adds arbitrary whitespace and optional newlines to a segment
    from a split TypeAtom string
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
    """
    Assuming `segment` has already been stirpped, re-add normalised
    whitespace ready for joining the segments into a TypeAtom str
    """
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


def assert_annotation_roundtrip(example: str, result: TypeAtom):
    normalised = _normalise_annotation(example)
    assert normalised == result.to_annotation()


@given(st_napoleon_type_annotation())
def test_type_atom(example):
    """
    Generate an arbitrary ('dirty') type annotation and check that we can
    make a round-trip comparison of it with the parsed result.
    """
    result = type_atom.parse(example)
    assert_annotation_roundtrip(example, result)


st_rest_of_line = st_strip_whitespace(min_size=0, max_size=80)


@st.composite
def st_arg_description_start(draw):
    """
    The rest-of-line that optionally follows an "arg (type)"

    Example:
        ": blah blah blah"
    """
    ws = draw(st_whitespace())
    trailer = draw(st_rest_of_line)
    return f":{ws}{trailer}"


@st.composite
def st_arg_name(draw):
    splat = draw(st.text('*', min_size=0, max_size=2))
    name = draw(st_python_identifier)
    return f"{splat}{name}"


@st.composite
def st_annotated_arg(draw):
    arg_name = draw(st_arg_name())
    whitespace = draw(st_whitespace(min_size=1))
    type_annotation = draw(st_napoleon_type_annotation())
    trailer = draw(
        st.one_of(
            st.just(''),
            st_arg_description_start(),
        )
    )
    return Example(
        f"{arg_name}{whitespace}({type_annotation}){trailer}",
        {
            'arg_name': arg_name,
            'whitespace': whitespace,
            'type_annotation': type_annotation,
            'trailer': trailer,
        }
    )


@given(annotated_arg_example=st_annotated_arg())
def test_arg_type_annotated(annotated_arg_example):
    """
    Test that we can parse the first line of an arg and its description
    and extract the arg name and a TypeAtom
    """
    example, context = annotated_arg_example
    parser = arg_type << rest_of_line
    result = parser.parse(example)
    assert result['arg'] == context['arg_name']
    assert_annotation_roundtrip(context['type_annotation'], result['type'])


@given(
    arg_name=st_arg_name(),
    trailer=st.one_of(
        st.just(''),
        st_arg_description_start(),
    )
)
def test_arg_type_no_annotation(arg_name, trailer):
    """
    Test that we can parse the first line of an arg and its description
    and extract the arg name, when there is no type annotation.
    """
    example = f"{arg_name}{trailer}"
    parser = arg_type << rest_of_line
    result = parser.parse(example)
    assert result['arg'] == arg_name


@st.composite
def st_rest_of_line_with_insertion(draw):
    """
    Insert something that looks like an args head in the middle of a line
    which should be ignored
    """
    line = draw(st_strip_whitespace(min_size=1, max_size=80))
    insertion_index = draw(st.integers(min_value=0, max_value=len(line)))
    head_name = draw(st_valid_args_section_name)
    return f"{line[:insertion_index]}{head_name}: {line[insertion_index:]}"


st_ignored_line = st.one_of(
    st_rest_of_line,
    st_rest_of_line_with_insertion(),
)


@given(
    indent=st_whitespace(),
    line_to_ignore=st_ignored_line,
)
def test_ignored_line(indent, line_to_ignore):
    """
    Test that we can parse an arbitrarily-indented line to ignore, without
    getting confused if it contains some text that looks like an 'args head'.
    (a real 'args head' must not have any text following the ":")
    """
    example = f"{indent}{line_to_ignore}\n"
    result = ignored_line.parse(example)
    assert result == ""


@given(
    indent=st_whitespace(),
    blank_lines=st.text('\n', min_size=0, max_size=2),
    ignored_lines=st_small_lists(st_ignored_line),
)
def test_ignored_lines(
    indent,
    blank_lines,
    ignored_lines,
):
    intro = "\n".join(f"{indent}{line}" for line in ignored_lines)
    to_be_consumed = f"{intro}\n{blank_lines}"
    tbc_line_count = Counter(to_be_consumed)["\n"]
    unconsumed = f"{indent}Args:\n{indent}{indent}key (str): blah"

    example = f"{to_be_consumed}{unconsumed}"

    parser = ignored_line.many()
    result, remainder = parser.parse_partial(example)
    assert result == [""] * tbc_line_count
    assert remainder == unconsumed


@st.composite
def st_annotated_arg_full(draw, initial_indent, indent):
    first_line, arg_context = draw(st_annotated_arg())
    wrapped_lines = draw(st_small_lists(st_rest_of_line))
    if wrapped_lines:
        continuation = "\n".join(
            f"{initial_indent}{indent*2}{indent}{line}"
            for line in wrapped_lines
        )
        return Example(
            f"{initial_indent}{indent}{first_line}\n{continuation}\n",
            arg_context
        )
    else:
        return Example(
            f"{initial_indent}{indent}{first_line}\n",
            arg_context
        )


@st.composite
def st_args_section(draw, initial_indent=None):
    """
    Header plus a list of annotated args
    """
    if initial_indent is None:
        initial_indent = draw(st_whitespace())
    if initial_indent:
        indent = initial_indent
    else:
        indent = draw(st_whitespace(min_size=2))

    args_head = draw(st_valid_args_head())
    annotated_args = draw(
        st_small_lists_nonempty(
            st_annotated_arg_full(initial_indent, indent),
            unique_by=lambda a: a.context['arg_name']
        )
    )
    args_str = "\n".join(arg[0] for arg in annotated_args)
    return Example(
        f"{initial_indent}{args_head}{args_str}",
        {
            'args_head': args_head,
            'annotated_args': annotated_args,
        }
    )


def _validate_args_section(result, context):
    assert result['name'] == 'Args'  # normalised "<any>" -> "Args"

    expected_arg_type_map: Dict[str, str] = {
        ex_arg.context['arg_name']: ex_arg.context['type_annotation']
        for ex_arg in context['annotated_args']
    }
    for result_item in result['items']:
        assert result_item['arg'] in expected_arg_type_map

        example = expected_arg_type_map.pop(result_item['arg'])
        assert_annotation_roundtrip(example, result_item['type'])

    assert not expected_arg_type_map


@given(st_args_section())
def test_p_arg_list(args_section):
    example, context = args_section
    result = p_arg_list.parse(example)
    _validate_args_section(result, context)


@st.composite
def st_annotated_return(draw):
    type_annotation = draw(st_napoleon_type_annotation())
    trailer = draw(
        st.one_of(
            st.just(''),
            st_arg_description_start(),
        )
    )
    return Example(
        f"{type_annotation}{trailer}",
        {
            'type_annotation': type_annotation,
            'trailer': trailer,
        }
    )


@st.composite
def st_annotated_return_full(draw, initial_indent, indent):
    first_line, context = draw(st_annotated_return())
    wrapped_lines = draw(st_small_lists(st_rest_of_line))
    if wrapped_lines:
        continuation = "\n".join(
            f"{initial_indent}{indent*2}{indent}{line}"
            for line in wrapped_lines
        )
        return Example(
            f"{initial_indent}{indent}{first_line}\n{continuation}\n",
            context
        )
    else:
        return Example(
            f"{initial_indent}{indent}{first_line}\n",
            context
        )


@st.composite
def st_returns_section(draw, initial_indent=None):
    """
    Header plus the return type with optional description
    """
    if initial_indent is None:
        initial_indent = draw(st_whitespace())
    if initial_indent:
        indent = initial_indent
    else:
        indent = draw(st_whitespace(min_size=2))

    returns_head = draw(st_valid_returns_head())
    annotated_return = draw(
        st_annotated_return_full(initial_indent, indent)
    )

    return Example(
        f"{initial_indent}{returns_head}{annotated_return[0]}",
        {
            'returns_head': returns_head,
            'annotated_return': annotated_return,
        }
    )


def _validate_returns_section(result, context):
    assert result['name'] in VALID_RETURNS_SECTION_NAMES
    assert result['name'] == VALID_RETURNS_SECTION_NAMES[result['name']][1]

    example = context['annotated_return'].context['type_annotation']
    result_type = result['items'][0]
    assert_annotation_roundtrip(example, result_type)


@given(st_returns_section())
def test_p_returns_block(returns_section):
    example, context = returns_section
    result = p_returns_block.parse(example)
    _validate_returns_section(result, context)


@st.composite
def st_napoleon_docstring(draw):
    initial_indent = draw(st_whitespace())

    intro = "\n".join(
        draw(st_small_lists(st_ignored_line))
    )
    # last ignored_line has no trailing \n
    gap_1 = draw(st.text('\n', min_size=1, max_size=3)) if intro else ''

    args_section = draw(
        st.one_of(
            st_args_section(initial_indent),
            st.just(Example('', {}))
        )
    )
    gap_2 = draw(st.text('\n', min_size=0, max_size=2)) if args_section[0] else ''

    returns_section = draw(
        st.one_of(
            st_returns_section(initial_indent),
            st.just(Example('', {}))
        )
    )
    gap_3 = draw(st.text('\n', min_size=0, max_size=2)) if returns_section[0] else ''

    following = "\n".join(
        draw(st_small_lists(st_ignored_line))
    )

    example = (
        f"{intro}"
        f"{gap_1}"
        f"{args_section[0]}"
        f"{gap_2}"
        f"{returns_section[0]}"
        f"{gap_3}"
        f"{following}"
    )
    return Example(
        example=example,
        context={
            'args_section': args_section,
            'returns_section': returns_section,
        }
    )


@given(st_napoleon_docstring())
def test_docstring_parser(docstring):
    example, context = docstring

    result = docstring_parser.parse(example)

    if context['args_section'][0]:
        note(f"args_section: {context['args_section'][0]}")
        _validate_args_section(
            result['args'],
            context['args_section'].context,
        )

    if context['returns_section'][0]:
        note(f"returns_section: {context['returns_section'][0]}")
        _validate_returns_section(
            result['returns'],
            context['returns_section'].context,
        )
