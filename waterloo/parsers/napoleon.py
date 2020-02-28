# import logging
import re
from collections import OrderedDict
from functools import partial

from megaparsy import char
from megaparsy.char.lexer import (
    indent_block,
    space,
    lexeme as megaparsy_lexeme,
    IndentMany,
    IndentSome,
    line_fold,
)
from megaparsy.control.applicative.combinators import between
import parsy

from waterloo.types import (
    ArgsSection,
    ArgTypes,
    ReturnType,
    TypeAtom,
    TypeDef,
    TypeSignature,
    VALID_ARGS_SECTION_NAMES,
    VALID_RETURNS_SECTION_NAMES,
)
from .python import python_identifier
from .utils import typed_mark


__all__ = ('docstring_parser', '_nested')


# logging.basicConfig(level=logging.DEBUG)


# UTILS

# parser which matches whitespace, including newline
scn = space(char.space1)

# parser which only matches ' ' and '\t', but *not* newlines
sc = parsy.regex(r'( |\t)*').result('')

_non_space = parsy.regex(r'\S')

# factory for parser returning tokens separated by no-newline whitespace
lexeme = partial(megaparsy_lexeme, p_space=sc)

rest_of_line = parsy.regex(r'.*')  # without DOTALL this will stop at a newline


# SECTION HEADERS

args_section_name = (
    parsy
    .regex(r'|'.join(VALID_ARGS_SECTION_NAMES))
    .result(ArgsSection.ARGS)  # normalise name
)

args_head = args_section_name << parsy.string(':') << (sc + char.eol)

returns_section_name = (
    parsy
    .regex(
        r'|'.join(
            pattern for pattern, _ in VALID_RETURNS_SECTION_NAMES.values()
        )
    )
    .map(lambda name: VALID_RETURNS_SECTION_NAMES[name][1])  # normalise name
)

returns_head = returns_section_name << parsy.string(':') << (sc + char.eol)


# PYTHON IDENTIFIERS

var_name = lexeme(
    parsy.regex(r'\*{0,2}') +
    python_identifier
)

# a dotted import module path to a python var name
dotted_var_path = lexeme(
    python_identifier
    .sep_by(parsy.string('.'), min=1)
    .combine(lambda *names: '.'.join(names))
)


@parsy.generate
def _nested() -> parsy.Parser:
    """
    Recursion helper for `type_atom`

    (looks for further type defs nested between `[` `]` pairs)
    """
    return (
        yield between(
            parsy.regex(r'\[\s*'),
            parsy.regex(r',?\s*\]'),  # allow line-breaks and trailing-comma
            type_atom.sep_by(parsy.regex(r',\s*')),  # includes new-lines
        )
    )


_type_token = dotted_var_path | parsy.string('...')

# mypy type definition, parsed into its nested components
type_atom = (
    parsy.seq(_type_token, _nested).combine(TypeAtom)
    | _type_token.map(lambda t: TypeAtom(t, []))
    | _nested  # recurse->
)


# in "Args" section the type def is in parentheses after the var name
arg_type_def = lexeme(
    parsy.string('(') >> typed_mark(type_atom, TypeDef) << parsy.regex(r'\)\:?')
)

# NOTE: parsy.seq with kwargs needs Python 3.6+
arg_type = parsy.seq(arg=var_name, type=arg_type_def.optional())

# in "Returns" section the type def is bare and there is no var name
# (description is not part of Napoleon spec but it's natural to provide one
# so we allow to parse a colon separator followed by optional description)
return_type = typed_mark(type_atom, TypeDef) << parsy.regex(r'\:?')


# SECTION PARSERS

def _line_fold_callback(sc_: parsy.Parser) -> parsy.Parser:
    """
    A 'line fold' is a follow-on line which is part of an indented item
    (See `line_fold` from megaparsy)

    Args:
        sc_: this space-consumer is generated by line_fold internals
            to handle indentation
    """
    @parsy.generate
    def _line_fold_callback_inner() -> parsy.Parser:
        """
        folded lines are the wrapped description for an arg
        """
        p_folded = ((_non_space + rest_of_line) << sc_)
        folded = yield p_folded.at_least(1)
        return folded

    return _line_fold_callback_inner << sc


p_line_fold = line_fold(scn, _line_fold_callback)


def indented_items(p_item: parsy.Parser) -> parsy.Parser:
    """
    Factory returning parser to consume the items within a section
    """

    @parsy.generate
    def _indented_items() -> IndentMany:
        head = yield p_item
        # in this case the `head` is the part of the item we care about
        # and `tail` is be the folded arg description, we discard it
        return IndentMany(indent=None, f=lambda _: head, p=p_line_fold)

    return _indented_items


def section(
    p_section_name: parsy.Parser,
    p_items: parsy.Parser,
) -> parsy.Parser:
    """
    Factory returning parser to consume a section and its indented items
    """

    @parsy.generate
    def _args_list_block() -> IndentSome:
        head = yield p_section_name << parsy.string(':') << sc
        return IndentSome(
            indent=None,
            f=lambda tail: {'name': head, 'items': tail},
            p=p_items,
        )

    return _args_list_block


p_arg_list = indent_block(
    scn,
    section(
        args_section_name,
        indent_block(scn, indented_items(arg_type << rest_of_line))
    )
).map(
    lambda section: ArgTypes.factory(
        name=section['name'],
        args=OrderedDict(
            (item['arg'], item['type'])
            for item in section['items']
        )
    )
)

p_returns_block = indent_block(
    scn,
    section(
        returns_section_name,
        indent_block(scn, indented_items(return_type << rest_of_line))
    )
).map(
    lambda section: ReturnType.factory(
        name=section['name'],
        type_def=section['items'][0] if section['items'] else None
    )
)


# consume any line that is not a section head that we care about (Args / Returns)
ignored_line = (
    (sc >> (args_head | returns_head)).should_fail('not section head') >>
    rest_of_line >>
    char.eol
).result('')


# THE PARSER
docstring_parser: parsy.Parser = (
    parsy.seq(
        arg_types=(ignored_line.many() >> p_arg_list).optional(),
        return_type=(ignored_line.many() >> p_returns_block).optional(),
    ).combine_dict(
        TypeSignature.factory
    )
    << parsy.regex(r'.*', re.DOTALL)
)
