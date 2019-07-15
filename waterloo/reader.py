import re

from bowler import Query


INDENT_SIZE = 4
INDENT = ' ' * INDENT_SIZE


IS_DOCSTRING_RE = re.compile(r"^(\"\"\"|''')")


def not_already_annotated(node, capture, filename):
    """
    if `firstnode` (the initial indent of first line in function body) contains
    as mypy type annotation comment then consider the func already annotated

    capture['initial_indent_node'] is a single element list 'because' we have
    used an alternation pattern (see `_indents` below) otherwise it would be
    a single node.
    """
    return not any(
        '# type:' in s
        for s in (
            capture['initial_indent_node'][0].prefix,
            capture['initial_indent_node'][0].get_suffix(),
        )
    )


def has_docstring(node, capture, filename):
    try:
        docstring_node = capture['docstring_parent_node'].children[0]
    except (AttributeError, IndexError):
        return False
    result = bool(IS_DOCSTRING_RE.search(docstring_node.value))
    capture['docstring'] = docstring_node.value
    return result


def print_matched(node, capture, filename):
    print(repr(node))
    print(capture['docstring'])
    print('')
    return node


_indents = "|".join("'%s'" % (INDENT * i) for i in range(1, 9))

q = (
    Query('junk/file_to_parse.py')
    .select(
        r"""
        funcdef< any* ':'
            suite< '\n'
                initial_indent_node=(%s)
                docstring_parent_node=simple_stmt< any* >
                any*
            >
        >
        """ % _indents
    )
    .filter(has_docstring)
    .filter(not_already_annotated)
    .modify(print_matched)
)
