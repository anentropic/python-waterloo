from collections import namedtuple
import re

import pytest

from .grammars.simple import grammar


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


def test_stackoverflow():
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
def test_parse(example):
    parsed = grammar.parseString(example)

    for i, expected_def in enumerate(expected):
        parsed_def = parsed[i]
        assert parsed_def.term == expected_def.term
        assert normalize(parsed_def.description) == expected_def.description
