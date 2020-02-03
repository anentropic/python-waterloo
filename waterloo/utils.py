import typing
from operator import itemgetter
from typing import cast, Iterable, List, Set

from waterloo.types import TypeAtom, Types, TypeSignature


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
    if signature.returns and signature.returns.type:
        returns = signature.returns.type.to_annotation()
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
    if isinstance(
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


def _get_typing_imports(type_names: Set[str]) -> str:
    return "from typing import {}".format(
        ", ".join(sorted(type_names))
    )


def _get_dotted_path_imports(type_names: Set[str]) -> List[str]:
    # isort will later collapse redundant import lines
    # i.e. different members from the same module
    return [
        "from {} import {}".format(*name.rsplit('.', maxsplit=1))
        for name in type_names
    ]


def get_import_lines(type_names: Set[str]) -> List[str]:
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

    Furthermore it is assumed we will fun `isort` on the resulting file, and
    perhaps `black`/`flake8`, to save us the hassle of trying to nicely format
    the inserted imports.
    """
    builtins = {name for name in type_names if _is_builtin_type(name)}
    type_names -= builtins
    typing_types = {name for name in type_names if _is_typing_type(name)}
    type_names -= typing_types
    dotted_paths = {name for name in type_names if _is_dotted_path(name)}
    type_names -= dotted_paths

    lines = [_get_typing_imports(typing_types)]
    lines.extend(_get_dotted_path_imports(dotted_paths))
    return lines
