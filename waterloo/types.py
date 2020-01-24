from typing import Iterable, NamedTuple, Union


def _repr_type_arg(arg):
    if isinstance(arg, str):
        return arg
    elif isinstance(arg, TypeAtom):
        return arg.to_annotation()
    elif isinstance(arg, Iterable):
        sub_args = ", ".join(_repr_type_arg(sub) for sub in arg)
        return f"[{sub_args}]"
    else:
        raise TypeError(arg)


class TypeAtom(NamedTuple):
    name: str
    args: Iterable[Union[str, 'TypeAtom']]

    def to_annotation(self):
        if self.args:
            args_annotations = _repr_type_arg(self.args)
            return f"{self.name}{args_annotations}"
        else:
            return self.name
