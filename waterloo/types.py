from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass, field
from enum import Enum
from typing import cast, Iterable, NamedTuple, Optional, Set, Union


class ArgsSection(str, Enum):
    ARGS = 'Args'


class ReturnsSection(str, Enum):
    RETURNS = 'Returns'
    YIELDS = 'Yields'


class Types(str, Enum):
    ELLIPSIS = '...'
    NONE = 'None'


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
    'Return': (r'Return(?!s)', ReturnsSection.RETURNS),
    'Returns': (r'Returns', ReturnsSection.RETURNS),
    'Yield': (r'Yield(?!s)', ReturnsSection.YIELDS),
    'Yields': (r'Yields', ReturnsSection.YIELDS),
}


def _repr_type_arg(
    arg: Union[str, 'TypeAtom', Iterable['TypeAtom']], fix_dotted_paths=True
) -> str:
    if isinstance(arg, str) or not arg:
        val = cast(str, arg) or ''
        if fix_dotted_paths and val != Types.ELLIPSIS:
            val = val.split('.')[-1]
        return val
    elif isinstance(arg, TypeAtom):
        return arg.to_annotation(fix_dotted_paths)
    elif isinstance(arg, Iterable):
        sub_args = ", ".join(
            _repr_type_arg(sub, fix_dotted_paths) for sub in arg
        )
        return f"[{sub_args}]"
    else:
        raise TypeError(arg)


class TypeAtom(NamedTuple):
    name: str
    args: Iterable['TypeAtom']  # type: ignore[misc]

    def to_annotation(self, fix_dotted_paths=True) -> str:
        name = _repr_type_arg(self.name, fix_dotted_paths)
        if self.args:
            args_annotations = _repr_type_arg(self.args, fix_dotted_paths)
            return f"{name}{args_annotations}"
        else:
            return name

    def type_names(self) -> Set[str]:
        """
        TODO:
        should Callable args list be a TypeAtom with name=None?
        (yes I think so)
        """
        names = set()
        names.add(self.name)
        for arg in self.args:
            if isinstance(arg, TypeAtom):
                names |= arg.type_names()
            else:
                for atom in arg:
                    names |= atom.type_names()
        return names


@dataclass
class ArgTypes:
    name: ArgsSection
    args: OrderedDict[str, Optional[TypeAtom]]

    is_fully_typed: bool = field(init=False)

    def __post_init__(self):
        """
        We need all args to have a type, otherwise we can't output a valid
        py2 type comment.

        TODO:
        For py3 we could potentially output annotations only for the args
        with specified types.
        Similarly for py2 we could output in this style:
        https://mypy.readthedocs.io/en/stable/python2.html#multi-line-python-2-function-annotations
        ...and then missing arg types would be acceptable. But that is harder
        to format...
        (in both cases these args will be treated as implicit `Any` by mypy)
        """
        self.is_fully_typed = all(
            arg is not None for arg in self.args.values()
        )

    def type_names(self) -> Set[str]:
        names: Set[str] = set()
        for arg in self.args.values():
            if arg:
                names |= arg.type_names()
        return names


@dataclass
class ReturnType:
    name: ReturnsSection
    type: Optional[TypeAtom]

    is_fully_typed: bool = field(init=False)

    def __post_init__(self):
        """
        (I'm not sure our parser would ever return a `ReturnType` with no
        `type` so this is likely always `True`)
        """
        self.is_fully_typed = self.type is not None

    def type_names(self) -> Set[str]:
        if self.type:
            return self.type.type_names()
        return set()


@dataclass
class TypeSignature:
    args: Optional[ArgTypes]
    returns: Optional[ReturnType]

    is_fully_typed: bool = field(init=False)

    def __post_init__(self):
        """
        If `self.returns is None` we can (optionally) assume the signature
        should be `-> None`. For everything else we require `is_fully_typed`.
        """
        self.is_fully_typed = (
            self.args and self.args.is_fully_typed
            and (
                self.returns is None
                or self.returns.is_fully_typed
            )
        )

    def type_names(self) -> Set[str]:
        names: Set[str] = set()
        if self.args:
            names |= self.args.type_names()
        if self.returns:
            names |= self.returns.type_names()
        return names
