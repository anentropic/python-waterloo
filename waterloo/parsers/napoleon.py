import logging
import re
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
    TypeAtom,
    VALID_ARGS_SECTION_NAMES,
    VALID_RETURNS_SECTION_NAMES,
)


logging.basicConfig(level=logging.DEBUG)


__all__ = ('docstring_parser',)


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
    .result('Args')  # normalise name
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

# a python var name
# (approximate support for Py3 unicode identifiers PEP-3131, see
# https://stackoverflow.com/questions/49100678/regex-matching-unicode-variable-names
# ...the regex is a bit too lenient accepting some chars that python doesn't)
@parsy.generate
def python_identifier():
    name = yield parsy.regex(r'[^\W0-9][\w]*')
    if name.isidentifier():
        return name
    else:
        yield parsy.fail("Not a valid python identifier")


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
def _nested():
    """
    Recursion helper for `type_atom`
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
    parsy.string('(') >> type_atom << parsy.regex(r'\)\:?')
)

# NOTE: parsy.seq with kwargs needs Python 3.6+
arg_type = parsy.seq(arg=var_name, type=arg_type_def.optional())

# in "Returns" section the type def is bare and there is no var name
# (description is not part of Napoleon spec but it's natural to provide one
# so we allow to parse a colon separator followed by optional description)
return_type = type_atom << parsy.regex(r'\:?')


# SECTION PARSERS

def _line_fold_callback(sc_):
    """
    A 'line fold' is a follow-on line which is part of an indented item
    (See `line_fold` from megaparsy)

    Args:
        sc_: this space-consumer is generated by line_fold internals
            to handle indentation
    """
    @parsy.generate
    def _line_fold_callback_inner():
        """
        folded lines are the wrapped description for an arg
        """
        p_folded = ((_non_space + rest_of_line) << sc_)
        folded = yield p_folded.at_least(1)
        return folded

    return _line_fold_callback_inner << sc


p_line_fold = line_fold(scn, _line_fold_callback)


def indented_items(p_arg_item):
    """
    Factory returning parser to consume the items within a section
    """

    @parsy.generate
    def _indented_items():
        head = yield p_arg_item
        # in this case the `head` is the part of the item we care about
        # and `tail` is be the folded arg description, we discard it
        return IndentMany(indent=None, f=lambda _: head, p=p_line_fold)

    return _indented_items


def section(p_section_name, p_arg_items):
    """
    Factory returning parser to consume a section and its indented items
    """

    @parsy.generate
    def _args_list_block():
        head = yield p_section_name << parsy.string(':') << sc
        return IndentSome(
            indent=None,
            f=lambda tail: {'name': head, 'items': tail},
            p=p_arg_items,
        )

    return _args_list_block


p_arg_list = indent_block(
    scn,
    section(
        args_section_name,
        indent_block(scn, indented_items(arg_type << rest_of_line))
    )
)

p_returns_block = indent_block(
    scn,
    section(
        returns_section_name,
        indent_block(scn, indented_items(return_type << rest_of_line))
    )
)


# consume any line that is not a section head that we care about (Args / Returns)
ignored_line = (
    (sc >> (args_head | returns_head)).should_fail('not section head') >>
    rest_of_line >>
    char.eol
).result('')


# THE PARSER
docstring_parser = (
    parsy.seq(
        args=(ignored_line.many() >> p_arg_list).optional(),
        returns=(ignored_line.many() >> p_returns_block).optional(),
    )
    << parsy.regex(r'.*', re.DOTALL)
)
