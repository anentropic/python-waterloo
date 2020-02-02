from operator import itemgetter
from typing import cast, Iterable

from waterloo.types import TypeAtom, TypeSignature


_type_getter = itemgetter('type')


def _join_type_atoms(type_atoms: Iterable[TypeAtom]) -> str:
    return ', '.join(atom.to_annotation() for atom in type_atoms)


def mypy_py2_annotation(signature: TypeSignature) -> str:
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
        args = '...'
    if signature.returns and signature.returns.type:
        returns = signature.returns.type.to_annotation()
    else:
        # TODO:
        # this is a reasonable default but it should be a configurable error
        returns = 'None'
    return f'# type: ({args}) -> {returns}'
