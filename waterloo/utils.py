import typing
from itertools import chain
from operator import itemgetter
from typing import cast, Dict, Iterable, Set, Tuple

from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.styles import Style

from waterloo.types import (
    ImportsForTypes,
    SourcePos,
    TypeAtom,
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
    if signature.args and signature.args.is_fully_typed:
        args = _join_type_atoms(
            cast(TypeAtom, atom) for atom in signature.args.args.values()
        )
    else:
        # TODO:
        # unless we are outputting
        # https://mypy.readthedocs.io/en/stable/python2.html#multi-line-python-2-function-annotations
        # then we should emit a warning here instead of this which
        # is like an implicit `Any` for all args
        args = Types.ELLIPSIS
    if signature.returns and signature.returns.type_def:
        returns = signature.returns.type_def.to_annotation()
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
    for name in dir(typing)
    if isinstance(  # type: ignore
        getattr(typing, name),
        (
            typing._GenericAlias,  # type: ignore[attr-defined,arg-type]
            typing._SpecialForm,
            typing.TypeVar,
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
        if start.row < end.row:
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


class StylePrinter:
    DEFAULT_STYLES = Style.from_dict({
        'debug': 'fg:ansigray',
        'info': 'fg:ansiwhite',
        'warning': 'fg:ansiyellow',
        'error': 'fg:ansired',
    })

    def __init__(self, style=DEFAULT_STYLES):
        self.style = style

    def debug(self, msg: str):
        self._print_level(msg, 'debug')

    def info(self, msg: str):
        self._print_level(msg, 'info')

    def warning(self, msg: str):
        self._print_level(msg, 'warning')

    def error(self, msg: str):
        self._print_level(msg, 'error')

    def _print_level(self, msg: str, level: str):
        self.print(f"<{level}>{msg}</{level}>")

    def print(self, msg: str):
        print_formatted_text(HTML(msg), style=self.style)
