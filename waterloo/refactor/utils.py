import typing
from enum import Enum, auto
from itertools import chain
from typing import cast, Callable, Dict, Generator, List, Optional, Set, Tuple

import inject
import parso

from waterloo.types import (
    ImportCollisionPolicy,
    ImportStrategy,
    LocalTypes,
    ModuleHasStarImportError,
    NameMatchesLocalClassError,
    NameMatchesRelativeImportError,
    NameToStrategy_T,
    NotFoundNoPathError,
    SourcePos,
    TypeAtom,
    TypeDef,
    Types,
    TypeSignature,
)


def get_type_comment(
    signature: TypeSignature, name_to_strategy: NameToStrategy_T
) -> str:
    """
    Args:
        signature: as per the result of `docstring_parser` containing
            details of the arg types and return type

    Returns:
        a mypy py2 type comment for a function (as a string)
    """
    if signature.arg_types and signature.arg_types.is_fully_typed:
        args = ", ".join(
            cast(TypeAtom, atom).to_annotation(name_to_strategy)
            for atom in signature.arg_types.args.values()
        )
    else:
        # to avoid reaching this case, configure ALLOW_UNTYPED_ARGS=False
        args = Types.ELLIPSIS
    if signature.return_type and signature.return_type.type_def:
        returns = signature.return_type.type_def.to_annotation(
            name_to_strategy
        )
    else:
        # to avoid reaching this case, configure REQUIRE_RETURN_TYPE=True
        returns = Types.NONE
    return f"# type: ({args}) -> {returns}"


BUILTIN_TYPE_NAMES = {
    name
    for name in __builtins__.keys()  # type: ignore[attr-defined]
    if not name.startswith("__") and isinstance(eval(name), type)
}

TYPING_TYPE_NAMES = {
    name
    for name in dir(typing)  # type: ignore
    if isinstance(
        getattr(typing, name),
        (
            typing._GenericAlias,  # type: ignore[attr-defined,arg-type]
            typing._SpecialForm,  # type: ignore
            typing.TypeVar,  # type: ignore
        )
    )
}


def _is_builtin_type(name: str) -> bool:
    return name in BUILTIN_TYPE_NAMES


def _is_typing_type(name: str) -> bool:
    return name in TYPING_TYPE_NAMES


def _is_dotted_path(name: str) -> bool:
    return '.' in name and name != Types.ELLIPSIS


def walk_tree(
    node: parso.tree.NodeOrLeaf
) -> Generator[parso.tree.NodeOrLeaf, None, None]:
    if hasattr(node, 'children'):
        yield node
        for child in node.children:
            for subchild in walk_tree(child):
                yield subchild
    else:
        yield node


@inject.params(settings='settings')
def find_local_types(filename: str, settings) -> LocalTypes:
    """
    TODO: parso understands scopes so we could feasibly
    determine visibility of non-top-level classdefs and imports
    (currently we find defs at all levels)
    TODO: if we don't do scopes maybe we should take top-level defs only
    """
    grammar = parso.load_grammar(version=settings.PYTHON_VERSION)
    with open(filename) as f:
        tree = grammar.parse(f.read(), path=filename)
    class_defs = set()
    star_imports = set()
    names_to_packages = {}
    package_imports = set()
    for node in walk_tree(tree):
        if isinstance(node, parso.python.tree.Class):
            class_defs.add(node.name.value)
        elif isinstance(node, parso.python.tree.ImportFrom):
            prefix = "." * node.level
            package = ".".join(name.value for name in node.get_from_names())
            if node.is_star_import():
                star_imports.add(f"{prefix}{package}")
            else:
                for name in node.get_defined_names():
                    names_to_packages[name.value] = f"{prefix}{package}"
        elif isinstance(node, parso.python.tree.ImportName):
            paths = node.get_paths()[0]
            package_imports.add(
                ".".join(path.value for path in paths)
            )
    return LocalTypes.factory(
        class_defs=class_defs,
        star_imports=star_imports,
        names_to_packages=names_to_packages,
        package_imports=package_imports,
    )


@inject.params(settings='settings')
def strategy_for_name_factory(
    local_types: LocalTypes,
    settings,
) -> Callable[[str], ImportStrategy]:
    """
    Args:
        local_types: names from imports or local ClassDefs
    """
    def _strategy_for_name(name: str) -> ImportStrategy:
        """
        We use the following heuristic to determine behaviour for auto-adding
        import statements where possible:

        1. primary decision table
                          | bare      | dotted path
        not found         | warn/fail | add import
        in locals         | use local | ? --> see 2. below
        module name found | N/A       | warn*/fail/from-style-import **
          in a * import   |           |

        2. decision table if dotted-path + type-name in locals:
        looks same path         | use existing
        looks different path    | import as dotted
        can't tell (e.g. locals | warn*/fail/import-as-dotted **
          name uses relative    |
          imports)              |

        * if not in builtins or typing
        ** configurably

        Raises:
            AmbiguousTypeError
        """
        if _is_dotted_path(name):
            module, name = name.rsplit(".", maxsplit=1)
            if name in local_types:
                local_module = local_types[name]
                if module == local_module:
                    # `module == local_module` means an exact match in imports
                    # i.e. from <apckage match> import <name match>
                    return ImportStrategy.USE_EXISTING
                elif local_module is None:
                    # `local_module is None` means local ClassDef
                    # if there is a local ClassDef and type has dotted path then
                    # maybe it was intended to disambiguate from the local cls?
                    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.IMPORT:
                        # the name was maybe already in scope but it's safe
                        # to add a specific import as well
                        return ImportStrategy.ADD_DOTTED
                    else:
                        # TODO in theory we could probably calculate the absolute
                        # import from filename + relative path, but it's awkward
                        raise NameMatchesLocalClassError(module, name)
                elif local_module.startswith("."):
                    # Relative import: "can't tell"
                    # we have a full path so we could add an import
                    # but it may be duplicating something already imported
                    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.IMPORT:
                        # the name was maybe already in scope but it's safe
                        # to add a specific import as well
                        return ImportStrategy.ADD_DOTTED
                    else:
                        # TODO in theory we could probably calculate the absolute
                        # import from filename + relative path, but it's awkward
                        raise NameMatchesRelativeImportError(module, name)
                else:
                    # "looks like different path"
                    return ImportStrategy.ADD_DOTTED
            else:
                # handle * imports? we could assume `name` is imported
                # if `from module import *` is present... BUT:
                # if `name.startswith("_")` it would be exempt
                # and `__all__` could break both of these assumptions
                # So... we treat any matching * import as AMBIGUOUS
                if module in local_types.star_imports:
                    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.IMPORT:
                        # the name was maybe already in scope but it's safe
                        # to add a specific import as well
                        return ImportStrategy.ADD_FROM
                    else:
                        raise ModuleHasStarImportError(module, name)
                else:
                    if module in local_types.package_imports:
                        return ImportStrategy.USE_EXISTING_DOTTED
                    else:
                        return ImportStrategy.ADD_FROM
        else:
            if name == Types.ELLIPSIS:
                return ImportStrategy.USE_EXISTING
            elif name in local_types:
                return ImportStrategy.USE_EXISTING
            elif _is_builtin_type(name):
                return ImportStrategy.USE_EXISTING
            elif _is_typing_type(name):
                return ImportStrategy.ADD_FROM
            else:
                # there's no possibility to add an import, so no AUTO option
                raise NotFoundNoPathError(None, name)

    return _strategy_for_name


def get_import_lines(
    strategies: Dict[ImportStrategy, Set[str]]
) -> Dict[Optional[str], Set[str]]:
    """
    This is best-effort... if you haven't used dotted paths when defining your
    docstring types then we will likely be missing imports needed for mypy
    checking to work.

    Furthermore it is assumed we will run `isort` on the resulting file, and
    perhaps `black`/`flake8`, to save us the hassle of trying too hard to
    nicely format the inserted imports, or deduplicate them etc.
    """
    import_tuples: List[Tuple[Optional[str], str]] = []

    def from_import(name: str) -> Tuple[str, str]:
        if _is_typing_type(name):
            return ("typing", name)
        else:
            return cast(Tuple[str, str], tuple(name.rsplit('.', maxsplit=1)))

    import_tuples.extend(
        from_import(name)
        for name in strategies.get(ImportStrategy.ADD_FROM, set())
    )

    import_tuples.extend(
        (None, name.rsplit(".", maxsplit=1)[0])
        for name in strategies.get(ImportStrategy.ADD_DOTTED, set())
    )

    imports_dict: Dict[str, Set[str]] = {}
    for left, right in import_tuples:
        imports_dict.setdefault(left, set()).add(right)

    return imports_dict


def slice_by_pos(val: str, start: SourcePos, end: SourcePos) -> str:
    """
    Slices the input string `val` and returns the portion between the
    `start` and `end` SourcePos markers.
    """
    if "\n" in val:
        lines = val.split("\n")
        if end.row > start.row:
            top = lines[start.row][start.col:]
            filling = lines[start.row + 1: end.row]
            bottom = lines[end.row][:end.col]
            return "\n".join(
                line for line in chain([top], filling, [bottom])
            )
        else:
            return lines[start.row][start.col:end.col]
    else:
        return val[start.col:end.col]


class TypeDefRole(Enum):
    ARG = auto()
    RETURN = auto()


def _remove_type_def(
    lines: List[str], type_def: TypeDef, offset: SourcePos, role: TypeDefRole
) -> List[str]:
    expand = 0
    if role is TypeDefRole.ARG:
        # we can assume the TypeDef is surrounded by parentheses
        expand = 1

    start_pos = type_def.start_pos + offset
    start_line = lines[start_pos.row]
    prefix = start_line[:start_pos.col - expand]
    if role is TypeDefRole.ARG:
        # remove preceding whitespace after arg name before open paren
        prefix = prefix.rstrip()

    end_pos = type_def.end_pos + offset
    end_line = lines[end_pos.row]
    _end = end_pos.col + expand
    if role is TypeDefRole.RETURN:
        if len(end_line) > _end and end_line[_end] == ":":
            _end += 1
    suffix = end_line[_end:].lstrip()

    replaced_line = f"{prefix}{suffix}"

    _pre = start_pos.row
    _post = end_pos.row + 1

    def has_return_description():
        # TODO: this would be easier if the parser captured a full AST...
        return (
            replaced_line.strip()
            or (lines[_post:]
                and lines[_post].startswith(prefix)  # is indented (else not part of returns section)
                and lines[_post].strip())
        )

    if role is TypeDefRole.RETURN:
        if not has_return_description():
            # if the return type had no description, remove the section header and
            # empty return type line, plus any preceding blank lines before header
            # NOTE: relies on current parser allows no lines between head + body
            _pre -= 1
            while _pre > 0 and lines[_pre - 1].strip() == "":
                _pre -= 1
            segments = [lines[:_pre], lines[_post:]]
        else:
            if replaced_line.strip():
                segments = [lines[:_pre], [replaced_line], lines[_post:]]
            else:
                segments = [lines[:_pre], lines[_post:]]
    else:
        segments = [lines[:_pre], [replaced_line], lines[_post:]]

    return [
        line
        for line in chain.from_iterable(segments)
    ]


def remove_types(docstring: str, signature: TypeSignature) -> str:
    """
    Returns:
        `docstring` with its type annotations removed
    """
    lines = docstring.split("\n")
    original_line_count = len(lines)
    offset = SourcePos(0, 0)
    if signature.arg_types:
        for type_def in signature.arg_types.args.values():
            if type_def is not None:
                lines = _remove_type_def(
                    lines=lines,
                    type_def=type_def,
                    offset=offset,
                    role=TypeDefRole.ARG,
                )
                line_count = len(lines)
                offset = SourcePos(line_count - original_line_count, 0)
    if signature.return_type and signature.return_type.type_def is not None:
        lines = _remove_type_def(
            lines=lines,
            type_def=signature.return_type.type_def,
            offset=offset,
            role=TypeDefRole.RETURN,
        )
    return "\n".join(lines)
