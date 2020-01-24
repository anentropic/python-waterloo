import re
from tokenize import tokenize, INDENT

from bowler import Query, LN, Capture, Filename

from waterloo.parsers.napoleon import docstring_parser
from waterloo.utils import mypy_py2_annotation


IS_DOCSTRING_RE = re.compile(r"^(\"\"\"|''')")


def not_already_annotated_py2(
    node: LN, capture: Capture, filename: Filename
) -> bool:
    """
    (filter)

    Filter out functions which appear to be already annotated with mypy
    Python 2 type comments.

    If `firstnode` (the initial indent of first line in function body) contains
    a mypy type annotation comment then consider the func already annotated

    `capture['initial_indent_node']` is a single element list 'because' we have
    used an alternation pattern (see `annotate_file` below) otherwise it would
    be a single node.
    """
    return '# type:' not in capture['initial_indent_node'][0].prefix


def has_docstring(node: LN, capture: Capture, filename: Filename) -> bool:
    """
    (filter)

    Filter out functions which don't have a docstring that we could parse
    for annotations.
    """
    try:
        docstring_node = capture['docstring_parent_node'].children[0]
    except (AttributeError, IndexError):
        return False
    result = bool(IS_DOCSTRING_RE.search(docstring_node.value))
    capture['docstring'] = docstring_node.value
    return result


def annotate_py2(node: LN, capture: Capture, filename: Filename) -> LN:
    """
    (modifier)

    Adds mypy type annotation comments for Python 2 code
    """
    inital_indent = capture['initial_indent_node'][0]
    print(capture['docstring'])
    # TODO: does not handle missing Returns: clause
    docstring_types = docstring_parser.parse(capture['docstring'])
    inital_indent.prefix = mypy_py2_annotation(docstring_types)
    return node


def _detect_indent(filename: str, default='    '):
    """
    This will take the first indent found in the file and use that as the
    model. In Python it is valid to have a different indentation style in
    every indented block in a file. But if you have code like that you don't
    deserve to have nice things! (waterloo won't match and annotate any
    functions which have different indent styles from the initial one)
    """
    with open('junk/file_to_parse.py', 'rb') as f:
        for token_info in tokenize(f.readline):
            if token_info.type == INDENT:
                return token_info.string
        else:
            # no indent found in file
            # (so there shouldn't be any functions to annotate
            # but we will return a default anyway...)
            return default


def annotate_file(filename: str, max_indent=8, **execute_kwargs):
    indent = _detect_indent(filename)
    indent_patterns = "|".join(
        "'%s'" % (indent * i) for i in range(1, max_indent + 1)
    )
    q = (
        Query(filename)
        .select(
            r"""
            funcdef< any* ':'
                suite< '\n'
                    initial_indent_node=(%s)
                    docstring_parent_node=simple_stmt< any* >
                    any*
                >
            >
            """ % indent_patterns
        )
        .filter(has_docstring)
        .filter(not_already_annotated_py2)
        .modify(annotate_py2)
    )
    q.execute(**execute_kwargs)
