from operator import itemgetter


_type_getter = itemgetter('type')


def _join_type_atoms(type_atoms):
    return ', '.join(
        type_atom_to_str(atom)
        for atom in type_atoms
    )


def type_atom_to_str(type_atom):
    # TODO: superseded by TypeAtom.to_annotation()
    if isinstance(type_atom, str):
        return type_atom
    elif isinstance(type_atom, list):
        # Callable
        args_string = _join_type_atoms(type_atom)
        return f'[{args_string}]'
    else:
        name, args = type_atom
        args_string = _join_type_atoms(args)
        return f'{name}[{args_string}]'


def mypy_py2_annotation(types_dict):
    """
    Args:
        types_dict: as per the result of `docstring_parser` containing
            details of the arg types and return type

    Returns:
        str: a mypy py2 type comment for a function
    """
    args = _join_type_atoms(
        map(_type_getter, types_dict['args']['items'])
    )
    returns = _join_type_atoms(types_dict['returns']['items'])
    return f'# type: ({args}) -> {returns}'
