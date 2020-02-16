import re
from functools import partial

from hypothesis import assume, strategies as st
from typing import Any, Dict, NamedTuple

from waterloo.types import (
    TypeAtom,
    SourcePos,
    VALID_ARGS_SECTION_NAMES,
    VALID_RETURNS_SECTION_NAMES,
)


class Example(NamedTuple):
    example: Any
    context: Dict[str, Any]


"""
A 'composite' strategy in Hypothesis effectively gives you a strategy factory.

To draw from a strategy you pass the strategy func, i.e. `draw(my_strategy).
To draw from a composite strategy you have to call it, i.e. `draw(composite())`

So to help differentiate plain strategies from composite ones I have named all
the composite strategies with `_f` suffix, for "factory".
"""

whitespace_char = st.text(' \t', min_size=1, max_size=1)

small_lists_f = partial(st.lists, min_size=0, max_size=3)
small_lists_nonempty_f = partial(st.lists, min_size=1, max_size=4)


@st.composite
def whitespace_f(draw, min_size=0, max_size=10):
    """
    homogenous whitespace of random type (space or tab) and random length
    (including zero, i.e. '')
    """
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    ws = draw(whitespace_char)
    return ws * n


@st.composite
def strip_whitespace_f(draw, *args, **kwargs):
    """
    Drawn from (by default) the full range of Hypothesis' `text` strategy
    but eliminating initial/trailing whitespace chars, including \n, but
    not from middle of string.
    """
    kwargs['alphabet'] = st.characters(blacklist_characters="\n\r")
    val = draw(st.text(*args, **kwargs))
    assume(val.strip() == val)
    return val


optional_newline = st.one_of(
    st.just(''),
    st.just('\n'),
)

invalid_section_head_template = st.one_of(
    st.just("{leading_whitespace}{section_name}:{trailing_whitespace}"),
    st.just("{leading_whitespace}{section_name}{trailing_whitespace}\n"),
)

valid_args_section_name = st.one_of(
    *(st.just(word) for word in VALID_ARGS_SECTION_NAMES)
)

invalid_args_section_name = st.text().filter(
    lambda t: t not in VALID_ARGS_SECTION_NAMES
)


VALID_SECTION_HEAD_TEMPLATE = "{section_name}:{trailing_whitespace}\n"


@st.composite
def valid_args_head_f(draw):
    section_name = draw(valid_args_section_name)
    trailing_whitespace = draw(whitespace_f())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def invalid_args_head_bad_name_f(draw):
    section_name = draw(invalid_args_section_name)
    trailing_whitespace = draw(whitespace_f())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def invalid_args_head_bad_template_f(draw):
    leading_whitespace = draw(whitespace_f())
    section_name = draw(valid_args_section_name)
    trailing_whitespace = draw(whitespace_f())
    template = draw(invalid_section_head_template)
    return template.format(
        leading_whitespace=leading_whitespace,
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


valid_returns_section_name = st.one_of(
    *(st.just(word) for word in VALID_RETURNS_SECTION_NAMES)
)

invalid_returns_section_name = st.text().filter(
    lambda t: t not in VALID_RETURNS_SECTION_NAMES
)


@st.composite
def valid_returns_head_f(draw):
    section_name = draw(valid_returns_section_name)
    trailing_whitespace = draw(whitespace_f())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def invalid_returns_head_bad_name_f(draw):
    section_name = draw(invalid_returns_section_name)
    trailing_whitespace = draw(whitespace_f())
    return VALID_SECTION_HEAD_TEMPLATE.format(
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


@st.composite
def invalid_returns_head_bad_template_f(draw):
    leading_whitespace = draw(whitespace_f())
    section_name = draw(valid_returns_section_name)
    trailing_whitespace = draw(whitespace_f())
    template = draw(invalid_section_head_template)
    return template.format(
        leading_whitespace=leading_whitespace,
        section_name=section_name,
        trailing_whitespace=trailing_whitespace,
    )


python_identifier = (
    st
    .from_regex(r'[^\W0-9][\w]*', fullmatch=True)
    .filter(lambda s: s.isidentifier())
)


@st.composite
def dotted_var_path_f(draw):
    segments = draw(small_lists_nonempty_f(python_identifier))
    return '.'.join(segments)


@st.composite
def noargs_typeatom_f(draw):
    return TypeAtom(
        name=draw(dotted_var_path_f()),
        args=(),
    )


@st.composite
def generic_typeatom_f(draw, children):
    """
    A type var with params (i.e. is 'generic'), without being one of the
    special cases such as homogenous tuple, callable (others?)

    Args:
        draw: provided by @st.composite
        children: another hypothesis strategy to draw from
            (first arg to function returned by decorator)
    """
    return TypeAtom(
        name=draw(dotted_var_path_f()),
        args=draw(small_lists_f(children))
    )


@st.composite
def homogenous_tuple_typeatom_f(draw, children):
    return TypeAtom(
        name='Tuple',
        args=(draw(children), TypeAtom('...', []))
    )


@st.composite
def callable_typeatom_f(draw, children):
    args_param = draw(small_lists_nonempty_f(children))
    returns_param = draw(children)
    return TypeAtom(
        name='Callable',
        args=(args_param, returns_param)
    )


@st.composite
def type_atom_f(draw):
    """
    Generate arbitrarily nested TypeAtom instances
    """
    example = draw(
        st.recursive(
            noargs_typeatom_f(),
            lambda children: st.one_of(
                children,
                generic_typeatom_f(children),
                homogenous_tuple_typeatom_f(children),
                callable_typeatom_f(children),
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
def napoleon_type_annotation_f(draw):
    """
    Generate a type annotation that you might find in a napoleon docstring
    made from a valid TypeAtom but with arbitrary whitespace in valid locations

    - after a `[`
    - after a `,`
    - before a `]`
    """
    type_atom = draw(type_atom_f())
    annotation = type_atom.to_annotation(False)
    return ''.join(
        _add_arbitrary_whitespace(
            segment=segment.strip(),
            whitespace=draw(whitespace_f()),
            newline=draw(optional_newline),
        )
        for segment in re.split(r'([\[\]\,])', annotation)
    )


rest_of_line = strip_whitespace_f(min_size=0, max_size=80)


@st.composite
def arg_description_start_f(draw):
    """
    The rest-of-line that optionally follows an "arg (type)"

    Example:
        ": blah blah blah"
    """
    ws = draw(whitespace_f())
    trailer = draw(rest_of_line)
    return f":{ws}{trailer}"


@st.composite
def arg_name_f(draw):
    splat = draw(st.text('*', min_size=0, max_size=2))
    name = draw(python_identifier)
    return f"{splat}{name}"


@st.composite
def annotated_arg_f(draw):
    arg_name = draw(arg_name_f())
    whitespace = draw(whitespace_f(min_size=1))
    type_annotation = draw(napoleon_type_annotation_f())
    trailer = draw(
        st.one_of(
            st.just(''),
            arg_description_start_f(),
        )
    )
    type_lines = type_annotation.split("\n")
    start_pos = SourcePos(
        row=0,
        col=len(arg_name) + len(whitespace) + 1
    )
    end_pos = SourcePos(
        row=0 + len(type_lines) - 1,
        col=len(type_lines[-1])
    )
    return Example(
        f"{arg_name}{whitespace}({type_annotation}){trailer}",
        {
            'arg_name': arg_name,
            'whitespace': whitespace,
            'type_annotation': type_annotation,
            'trailer': trailer,
            'start_pos': start_pos,
            'end_pos': end_pos,
        }
    )


@st.composite
def rest_of_line_with_insertion_f(draw):
    """
    Insert something that looks like an args head in the middle of a line
    which should be ignored
    """
    line = draw(strip_whitespace_f(min_size=1, max_size=80))
    insertion_index = draw(st.integers(min_value=0, max_value=len(line)))
    head_name = draw(valid_args_section_name)
    return f"{line[:insertion_index]}{head_name}: {line[insertion_index:]}"


ignored_line = st.one_of(
    rest_of_line,
    rest_of_line_with_insertion_f(),
)


@st.composite
def annotated_arg_full_f(draw, initial_indent, indent, row_offset=0):
    first_line, arg_context = draw(annotated_arg_f())
    wrapped_lines = draw(small_lists_f(rest_of_line))

    offset = SourcePos(row_offset, len(initial_indent) + len(indent))
    arg_context['start_pos'] += offset
    arg_context['end_pos'] += offset

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
def args_section_f(draw, initial_indent=None, row_offset=0):
    """
    Header plus a list of annotated args
    """
    if initial_indent is None:
        initial_indent = draw(whitespace_f())
    if initial_indent:
        indent = initial_indent
    else:
        indent = draw(whitespace_f(min_size=2))

    args_head = draw(valid_args_head_f())  # includes line-break
    annotated_args = draw(
        small_lists_nonempty_f(
            annotated_arg_full_f(
                initial_indent=initial_indent,
                indent=indent,
                row_offset=row_offset + 1,
            ),
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


@st.composite
def annotated_return_f(draw):
    type_annotation = draw(napoleon_type_annotation_f())
    trailer = draw(
        st.one_of(
            st.just(''),
            arg_description_start_f(),
        )
    )
    type_lines = type_annotation.split("\n")
    start_pos = SourcePos(
        row=0,
        col=0
    )
    end_pos = SourcePos(
        row=0 + len(type_lines) - 1,
        col=len(type_lines[-1])
    )
    return Example(
        f"{type_annotation}{trailer}",
        {
            'type_annotation': type_annotation,
            'trailer': trailer,
            'start_pos': start_pos,
            'end_pos': end_pos,
        }
    )


@st.composite
def annotated_return_full_f(draw, initial_indent, indent, row_offset=0):
    first_line, context = draw(annotated_return_f())
    wrapped_lines = draw(small_lists_f(rest_of_line))

    offset = SourcePos(row_offset, len(initial_indent) + len(indent))
    context['start_pos'] += offset
    context['end_pos'] += offset

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
def returns_section_f(draw, initial_indent=None, row_offset=0):
    """
    Header plus the return type with optional description
    """
    if initial_indent is None:
        initial_indent = draw(whitespace_f())
    if initial_indent:
        indent = initial_indent
    else:
        indent = draw(whitespace_f(min_size=2))

    returns_head = draw(valid_returns_head_f())
    annotated_return = draw(
        annotated_return_full_f(
            initial_indent=initial_indent,
            indent=indent,
            row_offset=row_offset + 1,
        )
    )

    return Example(
        f"{initial_indent}{returns_head}{annotated_return[0]}",
        {
            'returns_head': returns_head,
            'annotated_return': annotated_return,
        }
    )


@st.composite
def napoleon_docstring_f(draw):
    initial_indent = draw(whitespace_f())

    _intro_lines = draw(small_lists_f(ignored_line))
    intro = "\n".join(_intro_lines)
    # last ignored_line has no trailing \n
    gap_1 = draw(st.text('\n', min_size=1, max_size=3)) if intro else ''

    row_offset = len(_intro_lines) + len(gap_1)
    args_section = draw(
        st.one_of(
            args_section_f(initial_indent, row_offset=row_offset),
            st.just(Example('', {}))
        )
    )
    gap_2 = (
        draw(st.text('\n', min_size=0, max_size=2))
        if args_section[0]
        else ''
    )

    row_offset += len(args_section[0].split("\n")) + len(gap_2)
    returns_section = draw(
        st.one_of(
            returns_section_f(initial_indent, row_offset=row_offset),
            st.just(Example('', {}))
        )
    )
    gap_3 = (
        draw(st.text('\n', min_size=0, max_size=2))
        if returns_section[0]
        else ''
    )

    following = "\n".join(
        draw(small_lists_f(ignored_line))
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
