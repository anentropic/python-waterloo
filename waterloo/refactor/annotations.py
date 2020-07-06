from typing import Dict, Sequence

import inject
import parsy
from bowler import LN, Capture, Filename
from fissix.fixer_util import Newline
from fissix.pgen2 import token
from fissix.pygram import python_symbols as syms
from fissix.pytree import Leaf, Node
from structlog.threadlocal import bind_threadlocal, clear_threadlocal

from waterloo.conf.types import Settings
from waterloo.parsers.napoleon import docstring_parser
from waterloo.printer import StylePrinter
from waterloo.refactor.base import NonMatchingFixer, WaterlooQuery, interrupt_modifier
from waterloo.refactor.exceptions import Interrupt
from waterloo.refactor.reporter import (
    report_ambiguous_type_error,
    report_doc_args_signature_mismatch_error,
    report_generator_annotation,
    report_incomplete_arg_types,
    report_incomplete_return_type,
    report_parse_error,
    report_settings,
)
from waterloo.refactor.utils import (
    arg_names_from_signature,
    find_local_types,
    get_import_lines,
    get_type_comment,
    remove_types,
    strategy_for_name_factory,
)
from waterloo.types import (
    AmbiguousTypeError,
    ArgTypes,
    ImportStrategy,
    ReturnsSection,
    TypeSignature,
)


@inject.params(settings="settings", threadlocals="threadlocals")
def _init_threadlocals(filename, settings, threadlocals):
    threadlocals.settings = settings

    local_types = find_local_types(filename)
    threadlocals.strategy_for_name = strategy_for_name_factory(local_types)
    threadlocals.strategy_to_names = {}

    # per-file counters
    threadlocals.docstring_count = 0
    threadlocals.typed_docstring_count = 0
    threadlocals.comment_count = 0
    threadlocals.warning_count = 0
    threadlocals.error_count = 0

    # for the structlog logger (it manages its own threadlocals):
    clear_threadlocal()
    bind_threadlocal(filename=filename)


@inject.params(threadlocals="threadlocals")
def _cleanup_threadlocals(threadlocals):
    for key in list(threadlocals.__dict__.keys()):
        try:
            delattr(threadlocals, key)
        except AttributeError:
            pass
    # for the structlog logger:
    clear_threadlocal()


@inject.params(threadlocals="threadlocals")
def record_type_names(name_to_strategy: Dict[str, ImportStrategy], threadlocals):
    for name, strategy in name_to_strategy.items():
        threadlocals.strategy_to_names.setdefault(strategy, set()).add(name)


class StartFile(NonMatchingFixer):
    echo = inject.attr("echo")

    def start_tree(self, tree: Node, filename: str) -> None:
        self.echo.info(f"<b>{filename}</b>", verbose=False)
        _init_threadlocals(filename)


class EndFile(NonMatchingFixer):
    echo = inject.attr("echo")
    logger = inject.attr("log")
    threadlocals = inject.attr("threadlocals")

    def finish_tree(self, tree: Node, filename: str) -> None:
        if self.threadlocals.comment_count:
            self.logger.info(
                f"{self.threadlocals.comment_count} type comments added in file."
            )
            self.echo.info(
                f"➤➤ <b>{self.threadlocals.comment_count}</b> type comments added in file 🎉",
                verbose=False,
            )
        else:
            self.logger.info("no docstrings with annotatable types found in file.")
            self.echo.info(
                "➤➤ (no docstrings with annotatable types found in file)", verbose=False
            )

        if self.threadlocals.warning_count:
            self.logger.info(f"{self.threadlocals.warning_count} warnings in file.")
            self.echo.info(
                f"➤➤ <b>{self.threadlocals.warning_count}</b> warnings in file ⚠️",
                verbose=False,
            )

        if self.threadlocals.error_count:
            self.logger.info(f"{self.threadlocals.error_count} errors in file.")
            self.echo.info(
                f"➤➤ <b>{self.threadlocals.error_count}</b> errors in file 🛑",
                verbose=False,
            )

        self.echo.info("", verbose=False)
        _cleanup_threadlocals()


def f_not_already_annotated_py2(node: LN, capture: Capture, filename: Filename) -> bool:
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
    return "# type:" not in capture["initial_indent_node"].prefix


@interrupt_modifier
@inject.params(threadlocals="threadlocals")
def m_add_type_comment(
    node: LN, capture: Capture, filename: Filename, threadlocals
) -> LN:
    """
    (modifier)

    Adds type comment annotations for functions, as understood by
    `mypy --py2` type checking.
    """
    threadlocals.docstring_count += 1
    # since we filtered for funcs with a docstring, the initial_indent_node
    # should be the indent before the start of the docstring quotes.
    initial_indent = capture["initial_indent_node"]
    function = capture["function_name"]
    signature = capture["function_arguments"]

    try:
        doc_annotation = docstring_parser.parse(capture["docstring_node"].value)
    except parsy.ParseError as e:
        report_parse_error(e, function)
        raise Interrupt

    if not doc_annotation.has_types:
        raise Interrupt

    annotation_arg_names = (
        doc_annotation.arg_types.args.keys() if doc_annotation.arg_types else set()
    )
    signature_arg_names = arg_names_from_signature(signature)

    if doc_annotation.arg_types and not annotation_arg_names == signature_arg_names:
        report_doc_args_signature_mismatch_error(function)
        raise Interrupt
    # we either have no annotation args, or we do and the names match the signature

    # are we okay to annotate?
    # TODO these are currently WARN/FAIL... maybe should be OK/WARN/FAIL
    # configurably, like for amibiguous types
    if signature_arg_names and (
        not doc_annotation.arg_types or not doc_annotation.arg_types.is_fully_typed
    ):
        report_incomplete_arg_types(function)
        if not threadlocals.settings.ALLOW_UNTYPED_ARGS:
            raise Interrupt
    elif not signature_arg_names and not doc_annotation.arg_types:
        # special case: replace doc_annotation with one having empty args
        # (rather than `None`)
        doc_annotation = TypeSignature.factory(
            arg_types=ArgTypes.no_args_factory(),
            return_type=doc_annotation.return_type,
        )

    if not doc_annotation.return_type or not doc_annotation.return_type.is_fully_typed:
        report_incomplete_return_type(function)
        if threadlocals.settings.REQUIRE_RETURN_TYPE:
            raise Interrupt

    # yes, annotate...
    threadlocals.typed_docstring_count += 1

    # print(doc_annotation.return_type, doc_annotation.return_type.is_fully_typed, doc_annotation.return_type.name is ReturnsSection.YIELDS)
    if (
        doc_annotation.return_type
        and doc_annotation.return_type.is_fully_typed
        and doc_annotation.return_type.name is ReturnsSection.YIELDS
    ):
        report_generator_annotation(function)

    # record the types we found in this docstring
    # and warn/fail on ambiguous types according to IMPORT_COLLISION_POLICY
    name_to_strategy: Dict[str, ImportStrategy] = {}
    for name in doc_annotation.type_names():
        try:
            name_to_strategy[name] = threadlocals.strategy_for_name(name)
        except AmbiguousTypeError as e:
            report_ambiguous_type_error(e, function)
            if e.should_fail:
                raise Interrupt

    record_type_names(name_to_strategy)

    # add the type comment as first line of func body (before docstring)
    type_comment = get_type_comment(doc_annotation, name_to_strategy)
    initial_indent.prefix = f"{initial_indent}{type_comment}\n"
    threadlocals.comment_count += 1

    # remove types from docstring
    new_docstring_node = capture["docstring_node"].clone()
    new_docstring_node.value = remove_types(
        docstring=capture["docstring_node"].value, signature=doc_annotation,
    )
    capture["docstring_node"].replace(new_docstring_node)

    return node


def _find_import_pos(root: Node) -> int:
    """
    This logic cribbed from `fissix.fix_utils.touch_import`
    ...but we want to be able to output a single import line with multiple
    names imported from one package, so we'll use our own `_make_import_node`
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


def _make_from_import_node(
    left: str, right: Sequence[str], trailing_nl: bool = False
) -> Node:
    assert right  # non-empty
    name_leaves = [Leaf(token.NAME, right[0], prefix=" ")]
    name_leaves.extend(Leaf(token.NAME, name, prefix=", ") for name in right[1:])
    children = [
        Leaf(token.NAME, "from"),
        Leaf(token.NAME, left, prefix=" "),
        Leaf(token.NAME, "import", prefix=" "),
        Node(syms.import_as_names, name_leaves),
        Newline(),
    ]
    if trailing_nl:
        children.append(Newline())
    return Node(syms.import_from, children)


def _make_bare_import_node(name: str, trailing_nl: bool = False) -> Node:
    assert name  # non-empty
    children = [
        Leaf(token.NAME, "import"),
        Leaf(token.NAME, name, prefix=" "),
        Newline(),
    ]
    if trailing_nl:
        children.append(Newline())
    return Node(syms.import_name, children,)


class AddTypeImports(NonMatchingFixer):
    """
    Fixer that adds imports for all the `typing` and "dotted-path" types
    found in the document. We know that builtins don't need to be imported.
    We must then assume that all the remaining types are either defined in
    the file or already imported. If unrecognised types are specified in the
    docstring without a dotted path then how we treat the ambiguity is
    configured via IMPORT_COLLISION_POLICY and UNPATHED_TYPE_POLICY settings.
    """

    threadlocals = inject.attr("threadlocals")

    def finish_tree(self, tree: Node, filename: str) -> None:
        # TODO: what about name clash between dotted-path imports and
        # introspected locals?
        imports_dict = get_import_lines(self.threadlocals.strategy_to_names)
        insert_pos = _find_import_pos(tree)

        def _sort_key(val):
            left, right = val
            left = left or ""
            return (left, right)

        sorted_tuples = sorted(
            imports_dict.items(),
            key=_sort_key,
            reverse=True,  # because we insert last nodes first
        )
        for i, (left, right) in enumerate(sorted_tuples):
            if left:
                import_node = _make_from_import_node(
                    left=left,
                    right=sorted(right),
                    trailing_nl=i == 0 and insert_pos == 0,
                )
                tree.insert_child(insert_pos, import_node)
            else:
                for j, name in enumerate(right):
                    import_node = _make_bare_import_node(
                        name=name, trailing_nl=i == 0 and j == 0 and insert_pos == 0,
                    )
                    tree.insert_child(insert_pos, import_node)


@inject.params(settings="settings", echo="echo")
def annotate(
    *paths: str, settings: Settings = None, echo: StylePrinter = None, **execute_kwargs
):
    """
    Adds PEP-484 type comments to a set of files, with the import statements
    to support them. Quality of the output very much depends on quality of
    your docstrings.

    See https://pybowler.io/docs/api-query#execute for options.

    Args:
        *paths: files to process (dir paths are ok too)
        settings: dependency-injected settings object
        echo: dependency-injected pretty-printing logger
        **execute_kwargs: passed into the bowler `Query.execute()` method
    """
    report_settings()

    q = (
        WaterlooQuery(
            *paths, python_version=int(str(settings.PYTHON_VERSION).split(".", 1)[0]),
        )
        .select(
            r"""
            funcdef <
                'def' function_name=any
                function_parameters=parameters< '(' function_arguments=any* ')' >
                any* ':'
                suite < '\n'
                    initial_indent_node=any
                    simple_stmt < docstring_node=STRING any* >
                    any*
                >
            >
        """
        )
        .filter(f_not_already_annotated_py2)
        .modify(m_add_type_comment)
        .raw_fixer(StartFile)
        .raw_fixer(AddTypeImports)
        .raw_fixer(EndFile)
    )
    q.execute(**execute_kwargs)
