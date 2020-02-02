import re
from tokenize import tokenize, INDENT

from bowler import Query, LN, Capture, Filename

from waterloo.parsers.napoleon import docstring_parser
from waterloo.utils import get_type_comment


IS_DOCSTRING_RE = re.compile(r"^(\"\"\"|''')")


def not_already_annotated_py2(
    node: LN, capture: Capture, filename: Filename
) -> bool:
    """
    (filter)

    Filter out functions which appear to be already annotated with mypy
    Python 2 type comments.

    If `initial_indent_node` (the initial indent of first line in function
    body) contains a type comment then consider the func already annotated

    `capture['initial_indent_node']` is a single element list "because" we have
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

    Adds type comment annotations for functions, as understood by
    `mypy --py2` type checking.
    """
    # since we filtered for funcs with a docstring, the initial_indent_node
    # should be the indent before the start of the docstring quotes.
    initial_indent = capture['initial_indent_node'][0]

    # TODO: error handling
    signature = docstring_parser.parse(capture['docstring'])

    # add the type comment as first line of function body (before docstring)
    type_comment = get_type_comment(signature)
    initial_indent.prefix = f"{initial_indent}{type_comment}\n"
    return node


def _detect_indent(filename: str, default: str = '    ') -> str:
    """
    This will take the first indent found in the file and use that as the
    model. In Python it is valid to have a different indentation style in
    every indented block in a file. But if you have code like that you don't
    deserve to have nice things! (so waterloo won't match and annotate any
    functions which have different indent styles from the initial one)

    Returns:
        string containing the detected indent for the file
    """
    with open(filename, 'rb') as f:
        for token_info in tokenize(f.readline):
            if token_info.type == INDENT:
                return token_info.string
        else:
            # no indent found in file
            # (so there shouldn't be any functions to annotate
            # but we will return a default anyway...)
            return default


def annotate_file(filename: str, max_indent: int = 10, **execute_kwargs):
    """
    TODO:
    remove types from docstring a la:
    https://sphinxcontrib-napoleon.readthedocs.io/en/latest/#type-annotations
    sphinx can still render types in docs in this case thanks to:
    https://pypi.org/project/sphinx-autodoc-typehints/#using-type-hint-comments

    TODO:
    add imports for types
    """
    indent = _detect_indent(filename)
    # generate pattern-match for every indent level up to `max_indent`
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
