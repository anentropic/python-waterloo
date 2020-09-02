import pprint

from hypothesis import given, note, settings as hypothesis_settings

from tests.parsers import strategies
from waterloo.parsers.napoleon import docstring_parser
from waterloo.refactor.utils import remove_types


@hypothesis_settings(deadline=2500)
@given(strategies.napoleon_docstring_f())
def test_remove_types(docstring):
    example, context = docstring

    signature = docstring_parser.parse(example)
    result = remove_types(example, signature)

    expected = context["example_no_type"]

    note(f"signature: {pprint.pformat(signature)}")
    note(f"context: {pprint.pformat(context)}")
    note(f"example: {example!r}")
    note(f"result: {result!r}")
    note(f"expected: {expected!r}")

    assert result == expected
