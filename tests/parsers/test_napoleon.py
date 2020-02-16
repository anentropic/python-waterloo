from collections import OrderedDict

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
    type_atom,
)
from waterloo.types import (
    ArgsSection,
    ArgTypes,
    ReturnsSection,
    ReturnType,
    SourcePos,
    TypeAtom,
    TypeDef,
    TypeSignature,
)
from waterloo.annotator.utils import slice_by_pos

"""
Manually-constructed test-cases for the parsers

These are less exhaustive than the PBT tests but it's much easier
to see what is being parsed and expected output.
"""


def test_args_head():
    example = """Args:
"""
    result = args_head.parse(example)
    assert result == ArgsSection.ARGS

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
    ("str",
     TypeAtom("str", [])),
    ("Dict",
     TypeAtom("Dict", [])),
    ("Dict[int, str]",
     TypeAtom("Dict", [
        TypeAtom("int", []), TypeAtom("str", [])
     ])),
    ("Dict[int, db.models.User]",
     TypeAtom("Dict", [
        TypeAtom("int", []),
        TypeAtom("db.models.User", [])
     ])),
    ("my.generic.Container[int]",
     TypeAtom("my.generic.Container", [
        TypeAtom("int", [])
     ])),
    ("Tuple[int, ...]",
     TypeAtom("Tuple", [
        TypeAtom("int", []), TypeAtom("...", [])
     ])),
    ("Callable[[int, str], Dict[int, str]]",
     TypeAtom("Callable", [
        [TypeAtom("int", []),
         TypeAtom("str", [])],
        TypeAtom("Dict", [
            TypeAtom("int", []),
            TypeAtom("str", [])
        ])
     ])),
    ("""Tuple[
            int,
            str,
            ClassName
        ]""",
     TypeAtom("Tuple", [
        TypeAtom("int", []),
        TypeAtom("str", []),
        TypeAtom("ClassName", [])
     ])),
    ("""Tuple[
            int,
            str,
            ClassName,
        ]""",
     TypeAtom("Tuple", [
        TypeAtom("int", []),
        TypeAtom("str", []),
        TypeAtom("ClassName", [])
     ])),
])
def test_type_atom_valid(example, expected):
    result = type_atom.parse(example)
    assert result == expected


@pytest.mark.parametrize('example', [
    "Dict[int, str",
    "Dict[int, [db.models.User]",
    "Dict[int, [db.models.User]]]",
])
def test_type_atom_invalid(example):
    with pytest.raises(parsy.ParseError):
        type_atom.parse(example)


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
        'type': TypeDef(
            SourcePos(0, 5),
            TypeAtom('str', []),
            SourcePos(0, 8),
        )
    }

    assert result['type'].name == 'str'
    assert result['type'].args == []

    start, _, end = result['type']
    assert slice_by_pos(example, start, end) == 'str'


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
    assert section.name == ArgsSection.ARGS  # normalised -> "Args" (Enum)
    assert section.args == OrderedDict([
        ('key',
         TypeDef.from_tuples(
            (2, 17),
            ('str', []),
            (2, 20),
         )),
        ('num_tokens',
         TypeDef.from_tuples(
            (3, 24),
            ('int', []),
            (3, 27),
         )),
        ('timeout',
         TypeDef.from_tuples(
            (5, 21),
            ('int', []),
            (5, 24),
         )),
        ('retry_interval',
         TypeDef.from_tuples(
            (6, 28),
            ('Optional', [TypeAtom('float', [])]),
            (6, 43),
         )),
        ('*inner_args', None),
        ('**inner_kwargs', None),
    ])


def test_p_returns_block():
    example = """
        Yield:
            Optional[float]: how long to wait between polling
                for tokens to be available. `None` means use default interval
                which is equal to time needed to replenish `num_tokens`.
    """
    section = p_returns_block.parse(example)
    assert section.name == ReturnsSection.YIELDS  # normalised -> "Returns" (Enum)
    assert section.type_def == TypeDef.from_tuples(
        (2, 12),
        ('Optional', [TypeAtom('float', [])]),
        (2, 27),
    )


def test_docstring_parser():
    example = """
        Will block thread until `num_tokens` could be consumed from token bucket `key`.

        Keyword Arguments:
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
    expected = TypeSignature.factory(
        arg_types=ArgTypes.factory(
            name=ArgsSection.ARGS,
            args=OrderedDict([
                ('key',
                 TypeDef.from_tuples(
                    (4, 17),
                    ('str', []),
                    (4, 20),
                 )),
                ('num_tokens',
                 TypeDef.from_tuples(
                    (5, 24),
                    ('int', []),
                    (5, 27),
                 )),
                ('timeout',
                 TypeDef.from_tuples(
                    (7, 21),
                    ('int', []),
                    (7, 24),
                 )),
                ('retry_interval',
                 TypeDef.from_tuples(
                    (8, 28),
                    ('Optional', [TypeAtom('float', [])]),
                    (8, 43),
                 )),
            ]),
        ),
        return_type=ReturnType.factory(
            name=ReturnsSection.RETURNS,
            type_def=TypeDef.from_tuples(
                (13, 12),
                ('bool', []),
                (13, 16),
            ),
        )
    )

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
    expected = TypeSignature.factory(
        arg_types=ArgTypes.factory(
            name=ArgsSection.ARGS,
            args=OrderedDict([
                ('key',
                 TypeDef.from_tuples(
                    (4, 17),
                    ('str', []),
                    (4, 20),
                 )),
                ('num_tokens',
                 TypeDef.from_tuples(
                    (5, 24),
                    ('int', []),
                    (5, 27),
                 )),
                ('timeout',
                 TypeDef.from_tuples(
                    (7, 21),
                    ('int', []),
                    (7, 24),
                 )),
                ('retry_interval',
                 TypeDef.from_tuples(
                    (8, 28),
                    ('Optional', [TypeAtom('float', [])]),
                    (8, 43),
                 )),
            ]),
        ),
        return_type=ReturnType.factory(
            name=ReturnsSection.RETURNS,
            type_def=TypeDef.from_tuples(
                (13, 12),
                ("Tuple", [
                    TypeAtom("int", []),
                    TypeAtom("str", []),
                    TypeAtom("ClassName", [])
                ]),
                (17, 13),
            ),
        )
    )

    result = docstring_parser.parse(example)
    assert result == expected


def test_docstring_parser_no_annotations():
    example = """
        Will block thread until `num_tokens` could be consumed from token bucket `key`.

        key (str): identifying a specific token bucket

        bool: whether we got the requested tokens or not
            (False if timed out)
        """
    expected = TypeSignature.factory(
        arg_types=None,
        return_type=None,
    )

    result = docstring_parser.parse(example)
    assert result == expected