import typing
from enum import Enum
from itertools import chain
from operator import itemgetter
from typing import cast, Dict, Iterable, List, Set, Tuple

from waterloo.types import (
    ImportsForTypes,
    SourcePos,
    TypeAtom,
    TypeDef,
    Types,
    TypeSignature,
)


def _join_type_atoms(type_atoms: Iterable[TypeAtom]) -> str:
    return ', '.join(atom.to_annotation() for atom in type_atoms)


_type_getter = itemgetter('type')


def get_type_comment(signature: TypeSignature) -> str:
    """
    Args:
        signature: as per the result of `docstring_parser` containing
            details of the arg types and return type

    Returns:
        a mypy py2 type comment for a function
    """
    if signature.arg_types and signature.arg_types.is_fully_typed:
        args = _join_type_atoms(
            cast(TypeAtom, atom) for atom in signature.arg_types.args.values()
        )
    else:
        # TODO:
        # unless we are outputting
        # https://mypy.readthedocs.io/en/stable/python2.html#multi-line-python-2-function-annotations
        # then we should emit a warning here instead of this which
        # is like an implicit `Any` for all args
        args = Types.ELLIPSIS
    if signature.return_type and signature.return_type.type_def:
        returns = signature.return_type.type_def.to_annotation()
    else:
        # TODO:
        # this is a reasonable default but it should be a configurable error
        returns = Types.NONE
    return f'# type: ({args}) -> {returns}'


BUILTIN_TYPE_NAMES = {
    name
    for name in __builtins__.keys()  # type: ignore[attr-defined]
    if not name.startswith('__') and isinstance(eval(name), type)
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


def _is_builtin_type(name: str):
    return name in BUILTIN_TYPE_NAMES


def _is_typing_type(name: str):
    return name in TYPING_TYPE_NAMES


def _is_dotted_path(name: str):
    return '.' in name and name != Types.ELLIPSIS


def get_import_lines(type_names: Set[str]) -> ImportsForTypes:
    """
    We assume a type is either:
    - a builtin (e.g `str`, `int` etc)
    - a typing type (`Tuple`, `Dict` etc)
    - a dotted import path to a type (e.g. `my.module.ClassName` or
        `stdlib.module.typename`)
    - else already imported/defined in the document

    This is a half-arsed best-effort... if you haven't followed this heuristic
    when defining your docstring types then we will likely generate unnecessary
    imports or fail to import types needed for mypy checking to work.

    Furthermore it is assumed we will run `isort` on the resulting file, and
    perhaps `black`/`flake8`, to save us the hassle of trying to nicely format
    the inserted imports, or deduplicate them etc.
    """
    builtins = {name for name in type_names if _is_builtin_type(name)}
    type_names -= builtins

    typing_types = {name for name in type_names if _is_typing_type(name)}
    type_names -= typing_types

    dotted_paths = {name for name in type_names if _is_dotted_path(name)}
    type_names -= dotted_paths
    # assume remaining type_names are defined in the file or already imported

    import_tuples = [
        ('typing', name)
        for name in typing_types
    ]
    import_tuples.extend(
        cast(Tuple[str, str], tuple(name.rsplit('.', maxsplit=1)))
        for name in dotted_paths
    )
    imports_dict: Dict[str, Set[str]] = {}
    for left, right in import_tuples:
        imports_dict.setdefault(left, set()).add(right)

    return ImportsForTypes(
        imports=imports_dict,
        unimported=type_names,
    )


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
    ARG = 0
    RETURN = 1


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
