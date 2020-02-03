import os
import re
from threading import local
from tokenize import tokenize, INDENT
from typing import cast, List, Optional, Set, Type

from bowler import Capture, Filename, LN, Query
from fissix.fixer_base import BaseFix
from fissix.pytree import Node

from waterloo.parsers.napoleon import docstring_parser
from waterloo.utils import get_type_comment, get_import_lines


IS_DOCSTRING_RE = re.compile(r"^(\"\"\"|''')")

threadlocals = local()


def _detect_indent(filename: Filename, default: str = '    ') -> str:
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


def _get_type_names(filename: Filename) -> Set[str]:
    try:
        type_names = threadlocals.type_names
    except AttributeError:
        type_names = threadlocals.type_names = {}
    f_type_names = type_names.setdefault(filename, set())
    return f_type_names


def _record_type_names(filename: Filename, new_type_names: Set[str]) -> None:
    """
    NOTE:
    Bowler runs everything under multiprocessing, passing each file to be
    refactored into one of its pool of processes. As we have no other way of
    communicating between steps of the process or collating metadata we will
    just use a threadlocal var - this should be available to all code involved
    in processing a particular file.
    """
    type_names = _get_type_names(filename)
    type_names |= new_type_names
    threadlocals.type_names[filename] = type_names


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
    except (AttributeError, IndexError):
        return False
    result = bool(IS_DOCSTRING_RE.search(docstring_node.value))
    capture['docstring'] = docstring_node.value
    return result


def m_add_type_comment(node: LN, capture: Capture, filename: Filename) -> LN:
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

    _record_type_names(filename, signature.type_names())

    # add the type comment as first line of func body (before docstring)
    # TODO: convert dotted-path types to bare name
    type_comment = get_type_comment(signature)
    initial_indent.prefix = f"{initial_indent}{type_comment}\n"
    return node


class AddTypeImports(BaseFix):
    PATTERN = None  # type: ignore
    BM_compatible = False

    def match(self, node: LN) -> bool:
        # we don't need to participate in the matching phase, we just want
        # our `finish_tree` method to be called once after other modifiers
        # have completed their work...
        return False

    def transform(self, node: LN, capture: Capture) -> Optional[LN]:
        return node

    def finish_tree(self, tree: Node, filename: str):
        type_names = _get_type_names(cast(Filename, filename))
        imports = get_import_lines(type_names)
        print(f"LogTypesFixer[{os.getpid()}]: {type_names}")
        # TODO
        # insert imports as first child of tree node?
        # see https://github.com/jreese/fissix/blob/master/fissix/fixer_util.py#L123
        # > `FromImport`
        # implies we need different output from `get_import_lines`


class RawFixerQuery(Query):
    """
    Bowler's `Query.fixer()` method will take the fixer you give it and replace
    it with their own class. This means there are some things you could do
    with a custom fixer which won't be possible.

    So this class fixes that by allowing you to pass a custom Fixer that will
    be used as-is.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.raw_fixers: List[BaseFix] = []

    def raw_fixer(self, fx: Type[BaseFix]) -> "RawFixerQuery":
        self.raw_fixers.append(fx)
        return self

    def compile(self) -> List[Type[BaseFix]]:
        fixers = super().compile()
        fixers.extend(self.raw_fixers)
        return fixers


def annotate(*paths: str, max_indent_level: int = 10, **execute_kwargs):
    """
    TODO:
    remove types from docstring a la:
    https://sphinxcontrib-napoleon.readthedocs.io/en/latest/#type-annotations
    sphinx can still render types in docs in this case thanks to:
    https://pypi.org/project/sphinx-autodoc-typehints/#using-type-hint-comments

    TODO:
    add imports for types
    """
    indent = _detect_indent(paths[0])
    # generate pattern-match for every indent level up to `max_indent_level`
    indent_patterns = "|".join(
        "'%s'" % (indent * i) for i in range(1, max_indent_level + 1)
    )

    # TODO: Query can also accept a list of paths
    # (already handles the multiprocessing, with files distributed
    # to a pool of processes)
    q = (
        RawFixerQuery(*paths)
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
        .filter(f_has_docstring)
        .filter(f_not_already_annotated_py2)
        .modify(m_add_type_comment)
        .raw_fixer(AddTypeImports)
    )
    q.execute(**execute_kwargs)
