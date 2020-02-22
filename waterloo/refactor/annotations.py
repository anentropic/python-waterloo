import re
from threading import local
from typing import Sequence

import parsy
from bowler import Capture, Filename, LN
from fissix.fixer_util import Newline
from fissix.pgen2 import token
from fissix.pygram import python_symbols as syms
from fissix.pytree import Leaf, Node

from waterloo.conf import settings
from waterloo.parsers.napoleon import docstring_parser
from waterloo.refactor.base import (
    interrupt_modifier,
    NonMatchingFixer,
    WaterlooQuery,
)
from waterloo.refactor.exceptions import Interrupt
from waterloo.refactor.utils import (
    get_type_comment,
    get_import_lines,
    remove_types,
)
from waterloo.types import TypeSignature
from waterloo.utils import StylePrinter


echo = StylePrinter(settings.get('ECHO_STYLES'))


IS_DOCSTRING_RE = re.compile(r"^(\"\"\"|''')")

threadlocals = local()  # used in bowler subprocesses only


def _init_threadlocals():
    global threadlocals
    threadlocals.type_names = set()
    threadlocals.comment_count = 0


def _cleanup_threadlocals():
    global threadlocals
    try:
        del threadlocals.type_names
        del threadlocals.comment_count
    except AttributeError:
        pass


class StartFile(NonMatchingFixer):
    def start_tree(self, tree: Node, filename: str) -> None:
        echo.info(f"<b>{filename}</b>")
        _init_threadlocals()


class EndFile(NonMatchingFixer):
    def finish_tree(self, tree: Node, filename: str) -> None:
        if threadlocals.comment_count:
            echo.info(
                f"-> <b>{threadlocals.comment_count}</b> type comments added 🎉"
            )
        else:
            echo.info("(no docstring types found)")
        echo.info("")
        _cleanup_threadlocals()


def f_not_already_annotated_py2(
    node: LN, capture: Capture, filename: Filename
) -> bool:
    """
    (filter)

    Filter out functions which appear to be already annotated with mypy
    Python 2 type comments.

    If `initial_indent_node` (the initial indent of first line in function
    body) contains a type comment then consider the func already annotated

    `capture['initial_indent_node']` is a single element list "because" we
    have used an alternation pattern (see `annotate_file` below) otherwise
    it would be a single node.
    """
    return '# type:' not in capture['initial_indent_node'][0].prefix


def f_has_docstring(node: LN, capture: Capture, filename: Filename) -> bool:
    """
    (filter)

    Filter out functions which don't have a docstring that we could parse
    for annotations.
    """
    try:
        docstring_node = capture['docstring_parent_node'].children[0]
        result = bool(IS_DOCSTRING_RE.search(docstring_node.value))
    except (AttributeError, IndexError):
        return False
    capture['docstring_node'] = docstring_node
    return result


@interrupt_modifier
def m_add_type_comment(node: LN, capture: Capture, filename: Filename) -> LN:
    """
    (modifier)

    Adds type comment annotations for functions, as understood by
    `mypy --py2` type checking.
    """
    # since we filtered for funcs with a docstring, the initial_indent_node
    # should be the indent before the start of the docstring quotes.
    initial_indent = capture['initial_indent_node'][0]
    function = capture['function_name']

    try:
        signature = docstring_parser.parse(capture['docstring_node'].value)
    except parsy.ParseError as e:
        echo.error(
            f"🛑 <b>line {function.lineno}:</b> Error parsing docstring for <b>def {function.value}</b>\n"
            f"   {e!r}"
        )
        raise Interrupt

    if not signature.has_types:
        raise Interrupt

    # are we okay to annotate?
    if not signature.arg_types.is_fully_typed:
        if not settings.ALLOW_UNTYPED_ARGS:
            echo.error(
                f"🛑 <b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not fully specify arg types.\n"
                f"   (no type annotation added)"
            )
            raise Interrupt
        else:
            echo.warning(
                f"⚠️  <b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not fully specify arg types.\n"
                f"   -> args annotated as <b>(...)</b>"
            )

    if not signature.return_type or not signature.return_type.is_fully_typed:
        if settings.REQUIRE_RETURN_TYPE:
            echo.error(
                f"🛑 <b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not specify a return type.\n"
                f"   (no type annotation added)"
            )
            raise Interrupt
        else:
            echo.warning(
                f"⚠️  <b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not specify a return type.\n"
                f"   -> return annotated as <b>-> None</b>"
            )

    # yes, annotate...

    # record types found in this docstring
    threadlocals.type_names |= signature.type_names()

    # add the type comment as first line of func body (before docstring)
    type_comment = get_type_comment(signature)
    initial_indent.prefix = f"{initial_indent}{type_comment}\n"
    threadlocals.comment_count += 1

    # remove types from docstring
    new_docstring_node = capture['docstring_node'].clone()
    new_docstring_node.value = remove_types(
        docstring=capture['docstring_node'].value,
        signature=signature,
    )
    capture['docstring_node'].replace(new_docstring_node)

    return node


def _find_import_pos(root: Node) -> int:
    """
    This logic cribbed from `fissix.fix_utils.touch_import`
    ...but we want to be able to output a single import line with multiple
    names imported from one module, so we'll use our own `_make_import_node`
    """

    def _is_import(node: Node) -> bool:
        """Returns true if the node is an import statement."""
        return node.type in (syms.import_name, syms.import_from)

    def _is_import_stmt(node: Node) -> bool:
        return (
            node.type == syms.simple_stmt
            and node.children
            and _is_import(node.children[0])
        )

    # figure out where to insert the new import.  First try to find
    # the first import and then skip to the last one.
    insert_pos = offset = 0
    for idx, node in enumerate(root.children):
        if not _is_import_stmt(node):
            continue
        for offset, node2 in enumerate(root.children[idx:]):
            if not _is_import_stmt(node2):
                break
        insert_pos = idx + offset
        break

    # if there are no imports where we can insert, find the docstring.
    # if that also fails, we stick to the beginning of the file
    if insert_pos == 0:
        for idx, node in enumerate(root.children):
            if (
                node.type == syms.simple_stmt
                and node.children
                and node.children[0].type == token.STRING
            ):
                insert_pos = idx + 1
                break

    return insert_pos


def _make_import_node(left: str, right: Sequence[str]) -> Node:
    assert right  # non-empty
    name_leaves = [Leaf(token.NAME, right[0], prefix=" ")]
    name_leaves.extend(
        Leaf(token.NAME, name, prefix=", ")
        for name in right[1:]
    )
    children = [
        Leaf(token.NAME, "from"),
        Leaf(token.NAME, left, prefix=" "),
        Leaf(token.NAME, "import", prefix=" "),
        Node(syms.import_as_names, name_leaves),
        Newline(),
    ]
    return Node(syms.import_from, children)


class AddTypeImports(NonMatchingFixer):
    """
    Fixer that adds imports for all the `typing` and "dotted-path" types
    found in the document. We know that builtins don't need to be imported.
    We must then assume that all the remaining types are either defined in
    the file or already imported (for now it's "too hard" to try and detect
    if that is true... just run `mypy --py2` and get your errors).
    """

    def finish_tree(self, tree: Node, filename: str) -> None:
        imports_dict, unimported = get_import_lines(threadlocals.type_names)
        if unimported:
            echo.warning(
                "⚠️  Could not determine imports for these types: {}\n"
                "   (will assume types already imported or defined in file)".format(
                    f", ".join(
                        f"<b>{name}</b>"
                        for name in sorted(unimported)
                    )
                )
            )

        insert_pos = _find_import_pos(tree)
        for left, right in sorted(imports_dict.items(), reverse=True):
            import_node = _make_import_node(left, sorted(right))
            tree.insert_child(insert_pos, import_node)


def annotate(*paths: str, **execute_kwargs):
    """
    Adds PEP-484 type comments to a set of files, with the import statements
    to support them. Quality of the output very much depends on quality of
    your docstrings.

    See https://pybowler.io/docs/api-query#execute for options.

    Args:
        *paths: files to process (dir paths are ok too)
        project_indent: due to limits of bowler we can't really detect the
            indentation of the file and then use that in the `select` pattern
            like we'd need to, so let's hope you use consistent indentation
            throughout your project!
        max_indent_level: again because of bowler/lib2to3 limitation, we have
            to pre-generate pattern matches for all the indent levels in the
            document, but we can't measure it so just use an arbitrary large
            enough number.
        **execute_kwargs: passed into the bowler `Query.execute()` method
    """
    echo.debug("Running with options:")
    for key, val in settings.items():
        echo.debug(f"- {key}: <b>{val!r}</b>")
    echo.debug("")

    # generate pattern-match for every indent level up to `max_indent_level`
    indent_patterns = "|".join(
        "'%s'" % (settings.INDENT * i)
        for i in range(1, settings.MAX_INDENT_LEVEL + 1)
    )

    q = (
        WaterlooQuery(*paths)
        .select(
            r"""
            funcdef<
                'def' function_name=any
                any* ':'
                suite< '\n'
                    initial_indent_node=(%s)
                    docstring_parent_node=simple_stmt< any* >
                    any*
                >
            >
            """ % indent_patterns
        )
        .filter(f_has_docstring)
        .filter(f_not_already_annotated_py2)
        .modify(m_add_type_comment)
        .raw_fixer(StartFile)
        .raw_fixer(AddTypeImports)
        .raw_fixer(EndFile)
    )
    q.execute(**execute_kwargs)
