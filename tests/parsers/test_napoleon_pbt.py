import re
from collections import Counter, OrderedDict

import parsy
import pytest
from hypothesis import given, note, strategies as st
from typing import Dict

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
from waterloo.refactor.utils import slice_by_pos
from waterloo.types import (
    ArgsSection,
    TypeAtom,
    VALID_RETURNS_SECTION_NAMES,
)

from tests.parsers import strategies


"""
Property-based test-cases for the parsers

These are more exhaustive than the handwritten tests (and found some bugs
and edge cases which they did not) but they are harder to understand.
They are also reassuringly slow to run ;)
"""


@given(strategies.valid_args_head_f())
def test_valid_args_head(example):
    result = args_head.parse(example)
    assert result == "Args"  # (Section name has been normalised)


@given(st.one_of(
    strategies.invalid_args_head_bad_name_f(),
    strategies.invalid_args_head_bad_template_f(),
))
def test_invalid_args_head(example):
    with pytest.raises(parsy.ParseError):
        args_head.parse(example)


@given(strategies.valid_returns_head_f())
def test_valid_returns_head(example):
    result = returns_head.parse(example)
    assert result in VALID_RETURNS_SECTION_NAMES
    normalised = VALID_RETURNS_SECTION_NAMES[result][1]
    assert result == normalised  # (Section name has been normalised)


@given(st.one_of(
    strategies.invalid_returns_head_bad_name_f(),
    strategies.invalid_returns_head_bad_template_f(),
))
def test_invalid_returns_head(example):
    with pytest.raises(parsy.ParseError):
        returns_head.parse(example)


@given(
    splat=st.text('*', min_size=0, max_size=4),
    name=strategies.strip_whitespace_f(
        blacklist_characters="\n\r*", min_size=0, max_size=10
    ),
    trailing_ws=strategies.whitespace_f(),
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
    segments=strategies.small_lists_nonempty_f(st.text(min_size=0, max_size=8)),
    trailing_ws=strategies.whitespace_f(),
    newline=st.one_of(st.just(''), st.just('\n')),
)
def test_dotted_var_path(segments, trailing_ws, newline):
    """
    A dotted var path is a '.'-separated list of python identifiers
    optionally followed by non-newline whitespace
    not followed by a newline
    """
    # because `dotted_var_path` is built on megaparsy.lexeme it will strip
    # trailing whitespace, and in our test we are explicitly adding trailing
    # whitespace, so strip it from last segment if present
    if segments:
        segments[-1] = segments[-1].rstrip()

    path = '.'.join(segments)
    example = f"{path}{trailing_ws}{newline}"
    if all(seg.isidentifier() for seg in segments) and not newline:
        result = dotted_var_path.parse(example)
        assert result == path
    else:
        with pytest.raises(parsy.ParseError):
            dotted_var_path.parse(example)


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
    it should match the output from an equivalent TypeAtom.to_annotation(None)
    """
    return ''.join(
        _add_normalised_whitespace(segment.strip())
        for segment in re.split(r'([\[\]\,])', annotation)
    )


def assert_annotation_roundtrip(example: str, result: TypeAtom):
    normalised = _normalise_annotation(example)
    assert normalised == result.to_annotation(None)


@given(strategies.napoleon_type_annotation_f())
def test_type_atom(example):
    """
    Generate an arbitrary ('dirty') type annotation and check that we can
    make a round-trip comparison of it with the parsed result.
    """
    result = type_atom.parse(example)
    assert_annotation_roundtrip(example, result)


@given(annotated_arg_example=strategies.annotated_arg_f())
def test_arg_type_annotated(annotated_arg_example):
    """
    Test that we can parse the first line of an arg and its description
    and extract the arg name and a TypeDef
    """
    example, context = annotated_arg_example
    parser = arg_type << rest_of_line
    result = parser.parse(example)
    assert result['arg'] == context['arg_name']
    assert_annotation_roundtrip(context['type_annotation'], result['type'])

    start, _, end = result['type']
    assert slice_by_pos(example, start, end) == context['type_annotation']


@given(
    arg_name=strategies.arg_name_f(),
    trailer=st.one_of(
        st.just(''),
        strategies.arg_description_start_f(),
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


@given(
    indent=strategies.whitespace_f(),
    line_to_ignore=strategies.ignored_line,
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
    indent=strategies.whitespace_f(),
    blank_lines=st.text('\n', min_size=0, max_size=2),
    ignored_lines=strategies.small_lists_f(strategies.ignored_line),
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


def _validate_args_section(example, result, context):
    # normalised "<any valid>" -> "Args" (Enum)
    assert result.name == ArgsSection.ARGS

    expected_arg_type_map: Dict[str, str] = OrderedDict(
        (ex_arg.context['arg_name'], ex_arg.context['type_annotation'])
        for ex_arg in context['annotated_args']
    )
    assert expected_arg_type_map.keys() == result.args.keys()

    for name, result_type in result.args.items():
        type_annotation_str = expected_arg_type_map[name]
        assert_annotation_roundtrip(type_annotation_str, result_type)

        start, _, end = result_type
        assert slice_by_pos(example, start, end) == type_annotation_str


@given(strategies.args_section_f())
def test_p_arg_list(args_section):
    example, context = args_section
    result = p_arg_list.parse(example)
    _validate_args_section(example, result, context)


def _validate_returns_section(example, result, context):
    assert result.name in VALID_RETURNS_SECTION_NAMES
    assert result.name == VALID_RETURNS_SECTION_NAMES[result.name][1]

    type_annotation_str = context['annotated_return'].context['type_annotation']
    assert_annotation_roundtrip(type_annotation_str, result.type_def)

    start, _, end = result.type_def
    assert slice_by_pos(example, start, end) == type_annotation_str


@given(strategies.returns_section_f())
def test_p_returns_block(returns_section):
    example, context = returns_section
    result = p_returns_block.parse(example)
    note(repr(result))
    _validate_returns_section(example, result, context)


@given(strategies.napoleon_docstring_f())
def test_docstring_parser(docstring):
    example, context = docstring

    result = docstring_parser.parse(example)

    if context['args_section'][0]:
        note(f"args_section: {context['args_section'][0]}")
        _validate_args_section(
            example,
            result.arg_types,
            context['args_section'].context,
        )

    if context['returns_section'][0]:
        note(f"returns_section: {context['returns_section'][0]}")
        _validate_returns_section(
            example,
            result.return_type,
            context['returns_section'].context,
        )
