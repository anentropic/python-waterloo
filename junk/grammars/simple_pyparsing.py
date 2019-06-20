from functools import partial

import pyparsing as pp


NL = pp.LineEnd().suppress()
COLON = pp.Suppress(':')

STACK = [1]


def _flatten(tokens):
    # type: (pp.ParseResults) -> pp.ParseResults
    flattened = pp.ParseResults()
    for token in tokens:
        if isinstance(token, pp.ParseResults):
            flattened.extend(_flatten(token))
        else:
            flattened.append(token)
    return flattened


def flatten_and_join(join_str, tokens):
    # type: (str, pp.ParseResults) -> str
    return join_str.join(_flatten(tokens))


term = pp.Word(pp.alphanums + "_")

description = pp.Group(
    pp.restOfLine + NL +
    pp.Optional(
        pp.ungroup(
            ~pp.StringEnd() +
            pp.indentedBlock(pp.restOfLine, STACK)
        )
    )
)
description.addParseAction(partial(flatten_and_join, '\n'))

definition = pp.Group(
    term('term') + COLON + description('description')
)

grammar = pp.OneOrMore(definition)
