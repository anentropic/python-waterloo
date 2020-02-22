from __future__ import annotations
from collections import OrderedDict
from dataclasses import dataclass
from enum import Enum
from typing import (
    cast,
    Dict,
    Iterable,
    NamedTuple,
    Optional,
    Set,
    Tuple,
    Union,
)


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
    args: Iterable['TypeAtom']

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
        (...yes I think so)
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


class SourcePos(NamedTuple):
    row: int
    col: int

    def __add__(self, other):
        return SourcePos(
            self[0] + other[0],
            self[1] + other[1],
        )

    def __sub__(self, other):
        return SourcePos(
            self[0] - other[0],
            self[1] - other[1],
        )


class TypeDef(NamedTuple):
    start_pos: SourcePos
    type_atom: TypeAtom
    end_pos: SourcePos

    @classmethod
    def from_tuples(
        cls,
        start_pos: Tuple[int, int],
        type_atom: Tuple[str, Iterable[TypeAtom]],
        end_pos: Tuple[int, int],
    ) -> 'TypeDef':
        return cls(
            SourcePos(*start_pos),
            TypeAtom(*type_atom),
            SourcePos(*end_pos),
        )

    @property
    def name(self) -> str:
        return self.type_atom.name

    @property
    def args(self) -> Iterable[TypeAtom]:
        return self.type_atom.args

    def to_annotation(self, fix_dotted_paths=True) -> str:
        return self.type_atom.to_annotation(fix_dotted_paths)

    def type_names(self) -> Set[str]:
        return self.type_atom.type_names()


@dataclass(frozen=True)
class ArgTypes:
    name: ArgsSection
    args: OrderedDict[str, Optional[TypeDef]]

    is_fully_typed: bool

    @classmethod
    def factory(
        cls, name: ArgsSection, args: OrderedDict[str, Optional[TypeDef]]
    ) -> 'ArgTypes':
        """
        We need all args to have a type, otherwise we can't output a valid
        py2 type comment.
        """
        is_fully_typed = all(
            arg is not None for arg in args.values()
        )
        return cls(
            name=name,
            args=args,
            is_fully_typed=is_fully_typed,
        )

    def type_names(self) -> Set[str]:
        names: Set[str] = set()
        for arg in self.args.values():
            if arg:
                names |= arg.type_names()
        return names


@dataclass(frozen=True)
class ReturnType:
    name: ReturnsSection
    type_def: Optional[TypeDef]

    is_fully_typed: bool

    @classmethod
    def factory(
        cls, name: ReturnsSection, type_def: Optional[TypeDef]
    ) -> 'ReturnType':
        """
        (I'm not sure our parser would ever return a `ReturnType` with no
        `type_atom` so this is likely always `True`)
        """
        is_fully_typed = type_def is not None
        return cls(
            name=name,
            type_def=type_def,
            is_fully_typed=is_fully_typed,
        )

    def type_names(self) -> Set[str]:
        if self.type_def:
            return self.type_def.type_names()
        return set()


@dataclass(frozen=True)
class TypeSignature:
    arg_types: Optional[ArgTypes]
    return_type: Optional[ReturnType]

    has_types: bool
    is_fully_typed: bool

    @classmethod
    def factory(
        cls, arg_types: Optional[ArgTypes], return_type: Optional[ReturnType]
    ) -> 'TypeSignature':
        """
        If `return_type is None` we can (optionally) assume the signature
        should be `-> None`. For everything else we require `is_fully_typed`.
        """
        has_types = bool(arg_types or return_type)
        is_fully_typed = bool(
            arg_types and arg_types.is_fully_typed
            and (
                return_type is None
                or return_type.is_fully_typed
            )
        )
        return cls(
            arg_types=arg_types,
            return_type=return_type,
            has_types=has_types,
            is_fully_typed=is_fully_typed,
        )

    def type_names(self) -> Set[str]:
        names: Set[str] = set()
        if self.arg_types:
            names |= self.arg_types.type_names()
        if self.return_type:
            names |= self.return_type.type_names()
        return names


class ImportsForTypes(NamedTuple):
    imports: Dict[str, Set[str]]
    unimported: Set[str]
