from collections import namedtuple
from functools import partial
import re

import pyparsing as pp
import pytest


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


@pytest.fixture
def grammar():
    NL = pp.LineEnd().suppress()
    COLON = pp.Suppress(':')

    STACK = [1]

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

    return pp.OneOrMore(definition)


EXAMPLES = (
    pytest.param(
        """
    first_identifier: one line only
    identifier: some description text here which will wrap
        on to the next line. the follow-on text should be
        indented. the description may contain any text including
        identifier: in an awkward position like this
    next_identifier: more description, short this time
    last_identifier: blah blah
    """,
        id='indented_nl_indented_end'
    ),
    pytest.param(
        """
    first_identifier: one line only
    identifier: some description text here which will wrap
        on to the next line. the follow-on text should be
        indented. the description may contain any text including
        identifier: in an awkward position like this
    next_identifier: more description, short this time
    last_identifier: blah blah""",
        id='indented_no_nl_end'
    ),
    pytest.param(
        """
    first_identifier: one line only
    identifier: some description text here which will wrap
        on to the next line. the follow-on text should be
        indented. the description may contain any text including
        identifier: in an awkward position like this
    next_identifier: more description, short this time
    last_identifier: blah blah
""",
        id='indented_nl_non_indented_end'
    ),
    pytest.param(
        """
    first_identifier: one line only
    identifier: some description text here which will wrap
        on to the next line. the follow-on text should be
        indented. the description may contain any text including
        identifier: in an awkward position like this
    next_identifier: more description, short this time
    last_identifier: blah blah

""",
        id='indented_nl_blank_line_end'
    ),
    pytest.param(
        """
    first_identifier: one line only
    identifier: some description text here which will wrap
        on to the next line. the follow-on text should be
        indented. the description may contain any text including
        identifier: in an awkward position like this
    next_identifier: more description, short this time
    last_identifier: blah blah

    """,
        id='indented_nl_blank_line_indented_end'
    ),
    pytest.param(
        """
first_identifier: one line only
identifier: some description text here which will wrap
    on to the next line. the follow-on text should be
    indented. the description may contain any text including
    identifier: in an awkward position like this
next_identifier: more description, short this time
last_identifier: blah blah
    """,
        id='non_indented_nl_indented_end'
    ),
    pytest.param(
        """
first_identifier: one line only
identifier: some description text here which will wrap
    on to the next line. the follow-on text should be
    indented. the description may contain any text including
    identifier: in an awkward position like this
next_identifier: more description, short this time
last_identifier: blah blah""",
        id='non_indented_no_nl_end'
    ),
    pytest.param(
        """
first_identifier: one line only
identifier: some description text here which will wrap
    on to the next line. the follow-on text should be
    indented. the description may contain any text including
    identifier: in an awkward position like this
next_identifier: more description, short this time
last_identifier: blah blah
""",
        id='non_indented_nl_non_indented_end'
    ),
    pytest.param(
        """
first_identifier: one line only
identifier: some description text here which will wrap
    on to the next line. the follow-on text should be
    indented. the description may contain any text including
    identifier: in an awkward position like this
next_identifier: more description, short this time
last_identifier: blah blah

""",
        id='non_indented_nl_blank_line_end'
    ),
    pytest.param(
        """
first_identifier: one line only
identifier: some description text here which will wrap
    on to the next line. the follow-on text should be
    indented. the description may contain any text including
    identifier: in an awkward position like this
next_identifier: more description, short this time
last_identifier: blah blah

    """,
        id='non_indented_nl_blank_line_indented_end'
    ),
    pytest.param(
        """first_identifier: one line only
identifier: some description text here which will wrap
    on to the next line. the follow-on text should be
    indented. the description may contain any text including
    identifier: in an awkward position like this
next_identifier: more description, short this time
last_identifier: blah blah""",
        id='non_indented_tight_quotes'
    ),
)


Definition = namedtuple('Definition', 'term description')

expected = (
    Definition(
        'first_identifier',
        'one line only'
    ),
    Definition(
        'identifier',
        'some description text here which will wrap on to the next line. the follow-on text should be indented. the description may contain any text including identifier: in an awkward position like this'
    ),
    Definition(
        'next_identifier',
        'more description, short this time'
    ),
    Definition(
        'last_identifier',
        'blah blah'
    ),
)


def normalize(val):
    return re.sub(r'\s+', ' ', val).strip()


def test_stackoverflow(grammar, ):
    """
    Simpler example text
    """
    example = """
identifier: some description text here which will wrap
    on to the next line. the follow-on text should be
    indented. it may contain identifier: and any text
    at all is allowed
next_identifier: more description, short this time
last_identifier: blah blah
"""
    expected = (
        Definition(
            'identifier',
            'some description text here which will wrap on to the next line. the follow-on text should be indented. it may contain identifier: and any text at all is allowed'
        ),
        Definition(
            'next_identifier',
            'more description, short this time'
        ),
        Definition(
            'last_identifier',
            'blah blah'
        ),
    )
    parsed = grammar.parseString(example)

    for i, expected_def in enumerate(expected):
        parsed_def = parsed[i]
        assert parsed_def.term == expected_def.term
        assert normalize(parsed_def.description) == expected_def.description


@pytest.mark.parametrize('example', EXAMPLES)
def test_parse(grammar, example):
    parsed = grammar.parseString(example)

    for i, expected_def in enumerate(expected):
        parsed_def = parsed[i]
        assert parsed_def.term == expected_def.term
        assert normalize(parsed_def.description) == expected_def.description
