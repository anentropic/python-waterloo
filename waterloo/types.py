from typing import Iterable, NamedTuple, Union


# https://sphinxcontrib-napoleon.readthedocs.io/en/latest/#docstring-sections
VALID_ARGS_SECTION_NAMES = {
    'Args',
    'Kwargs',  # not an official part of Napoleon spec but frequently used
    'Arguments',
    'Keyword Args',
    'Keyword Arguments',
    'Parameters',
}

VALID_RETURNS_SECTION_NAMES = {
    'Return': (r'Return(?!s)', 'Returns'),
    'Returns': (r'Returns', 'Returns'),
    'Yield': (r'Yield(?!s)', 'Yields'),
    'Yields': (r'Yields', 'Yields'),
}


T_TypeAtomArgs = Iterable[Union[str, 'TypeAtom']]


def _repr_type_arg(arg: Union[str, 'TypeAtom', T_TypeAtomArgs]) -> str:
    if isinstance(arg, str) or not arg:
        return arg or ''
    elif isinstance(arg, TypeAtom):
        return arg.to_annotation()
    elif isinstance(arg, Iterable):
        sub_args = ", ".join(_repr_type_arg(sub) for sub in arg)
        return f"[{sub_args}]"
    else:
        raise TypeError(arg)


class TypeAtom(NamedTuple):
    name: str
    args: T_TypeAtomArgs

    def to_annotation(self) -> str:
        if self.args:
            args_annotations = _repr_type_arg(self.args)
            return f"{self.name}{args_annotations}"
        else:
            return self.name
