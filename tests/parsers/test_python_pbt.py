import parsy
import pytest
from hypothesis import given, strategies as st

from waterloo.parsers.python import python_identifier


"""
Property-based test-cases for the parsers

These are more exhaustive than the handwritten tests (and found some bugs
and edge cases which they did not) but they are harder to understand.
They are also reassuringly slow to run ;)
"""


@given(st.text(min_size=1, max_size=8))
def test_python_identifier(example):
    if example.isidentifier():
        result = python_identifier.parse(example)
        assert result == example
    else:
        with pytest.raises(parsy.ParseError):
            python_identifier.parse(example)
