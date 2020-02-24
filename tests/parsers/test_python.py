import parsy
import pytest

from waterloo.parsers.python import python_identifier

"""
Manually-constructed test-cases for the parsers

These are less exhaustive than the PBT tests but it's much easier
to see what is being parsed and expected output.

(over time I have also pasted some adversarial examples that Hypothesis
found into these cases as a quick way to iterate on fixing them....)
"""


@pytest.mark.parametrize('example', [
    "str",
    "Dict",
    "var_1_2_abc",
    "ClassName",
    b'A\xf3\xa0\x84\x80'.decode('utf8'),  # looks like "A", isidentifier()=True
    "A፩",
    "args",
    "kwargs",
])
def test_python_identifier_valid(example):
    result = python_identifier.parse(example)
    assert result == example


@pytest.mark.parametrize('example', [
    "dotted.path",
    "1name",
    "no-hyphens",
    "one two three",
    "A (A)",
    "*args",  # the identifier would just be "args"
    "str  ",
    "Dict\t",
])
def test_python_identifier_invalid(example):
    with pytest.raises(parsy.ParseError):
        python_identifier.parse(example)
