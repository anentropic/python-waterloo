from __future__ import annotations

import logging
from collections.abc import Iterable as IterableABC
from dataclasses import dataclass
from enum import Enum, auto
from functools import singledispatch
from typing import Dict, Iterable, NamedTuple, Optional, Set, Tuple

import inject
from typing_extensions import Final


class ArgsSection(str, Enum):
    ARGS = "Args"


class ReturnsSection(str, Enum):
    RETURNS = "Returns"
    YIELDS = "Yields"


class Types(str, Enum):
    ELLIPSIS = "..."
    NONE = "None"


# https://sphinxcontrib-napoleon.readthedocs.io/en/latest/#docstring-sections
VALID_ARGS_SECTION_NAMES: Final = {
    "Args",
    "Kwargs",  # not an official part of Napoleon spec but frequently used
    "Arguments",
    "Keyword Args",
    "Keyword Arguments",
    "Parameters",
}

VALID_RETURNS_SECTION_NAMES: Final = {
    "Return": (r"Return(?!s)", ReturnsSection.RETURNS),
    "Returns": (r"Returns", ReturnsSection.RETURNS),
    "Yield": (r"Yield(?!s)", ReturnsSection.YIELDS),
    "Yields": (r"Yields", ReturnsSection.YIELDS),
}

NameToStrategy_T = Dict[str, "ImportStrategy"]


class TypeAtom(NamedTuple):
    name: str
    args: Iterable["TypeAtom"]

    def to_annotation(self, name_to_strategy: Optional[NameToStrategy_T]) -> str:
        name = _repr_type_arg(self.name, name_to_strategy)
        if self.args:
            args_annotations = _repr_type_arg(self.args, name_to_strategy)
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


def should_strip_path(name: str, strategy: Optional[ImportStrategy]) -> bool:
    return name != Types.ELLIPSIS and strategy not in DOTTED_PATH_STRATEGIES


@singledispatch
def _repr_type_arg(val, name_to_strategy: Optional[NameToStrategy_T]) -> str:
    """
    Helper for representing a TypeAtom as a type annotation
    """
    # default case - we should have implementations registered for all
    # expected types.
    raise TypeError(val)


@_repr_type_arg.register
def _(name: str, name_to_strategy: Optional[NameToStrategy_T]) -> str:
    """
    By default we will strip dotted package prefix from type name,
    unless we find ImportStrategy.ADD_DOTTED
    """
    # `val` is the name from TypeAtom
    if name_to_strategy is not None and should_strip_path(
        name, name_to_strategy.get(name)
    ):
        name = name.rsplit(".", maxsplit=1)[-1]
    return name


@_repr_type_arg.register
def _(atom: TypeAtom, name_to_strategy: Optional[NameToStrategy_T]) -> str:
    return atom.to_annotation(name_to_strategy)


@_repr_type_arg.register(IterableABC)
def _(
    type_args: Iterable[TypeAtom], name_to_strategy: Optional[NameToStrategy_T]
) -> str:
    if not type_args:
        return ""
    # recurse
    sub_args = ", ".join(_repr_type_arg(sub, name_to_strategy) for sub in type_args)
    return f"[{sub_args}]"


class SourcePos(NamedTuple):
    row: int
    col: int

    def __add__(self, other):
        return SourcePos(self[0] + other[0], self[1] + other[1],)

    def __sub__(self, other):
        return SourcePos(self[0] - other[0], self[1] - other[1],)


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
    ) -> "TypeDef":
        return cls(SourcePos(*start_pos), TypeAtom(*type_atom), SourcePos(*end_pos),)

    @property
    def name(self) -> str:
        return self.type_atom.name

    @property
    def args(self) -> Iterable[TypeAtom]:
        return self.type_atom.args

    def to_annotation(self, name_to_strategy: Optional[NameToStrategy_T]) -> str:
        return self.type_atom.to_annotation(name_to_strategy)

    def type_names(self) -> Set[str]:
        return self.type_atom.type_names()


@dataclass(frozen=True)
class ArgTypes:
    name: ArgsSection
    args: Dict[str, Optional[TypeDef]]

    is_fully_typed: bool

    @classmethod
    def factory(
        cls, name: ArgsSection, args: Dict[str, Optional[TypeDef]]
    ) -> "ArgTypes":
        """
        We need all args to have a type, otherwise we can't output a valid
        py2 type comment. This is indicated by `is_fully_typed`.
        """
        is_fully_typed = all(arg is not None for arg in args.values())
        return cls(name=name, args=args, is_fully_typed=is_fully_typed,)

    @classmethod
    def no_args_factory(cls) -> "ArgTypes":
        """
        For a function with no args in its real signature.
        """
        return cls(name=ArgsSection.ARGS, args={}, is_fully_typed=True,)

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
    def factory(cls, name: ReturnsSection, type_def: Optional[TypeDef]) -> "ReturnType":
        """
        (I'm not sure our parser would ever return a `ReturnType` with no
        `type_atom` so `is_fully_typed` is likely always `True`)
        """
        is_fully_typed = type_def is not None
        return cls(name=name, type_def=type_def, is_fully_typed=is_fully_typed,)

    def type_names(self) -> Set[str]:
        if self.type_def:
            names = self.type_def.type_names()
            if self.name is ReturnsSection.YIELDS:
                names.add("Generator")
            return names
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
    ) -> "TypeSignature":
        """
        If `return_type is None` we can (optionally) assume the signature
        should be `-> None`. For everything else we require `is_fully_typed`.
        """
        has_types = bool(arg_types or return_type)
        is_fully_typed = bool(
            arg_types
            and arg_types.is_fully_typed
            and (return_type is None or return_type.is_fully_typed)
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


@dataclass(frozen=True)
class LocalTypes:
    type_defs: Set[str]
    star_imports: Set[str]
    names_to_packages: Dict[str, str]
    package_imports: Set[str]

    all_names: Set[str]

    @classmethod
    def empty(cls) -> "LocalTypes":
        return cls(
            type_defs=set(),
            star_imports=set(),
            names_to_packages={},
            package_imports=set(),
            all_names=set(),
        )

    def update_all_names(self):
        self.all_names.update(self.type_defs | self.names_to_packages.keys())

    @classmethod
    def factory(
        cls,
        type_defs: Set[str],
        star_imports: Set[str],
        names_to_packages: Dict[str, str],
        package_imports: Set[str],
    ) -> "LocalTypes":
        # should be no overlap in names, that would be a bug in the src file!
        assert not type_defs & names_to_packages.keys()
        return cls(
            type_defs=type_defs,
            star_imports=star_imports,
            names_to_packages=names_to_packages,
            package_imports=package_imports,
            all_names=type_defs | names_to_packages.keys(),
        )

    def __contains__(self, name) -> bool:
        return name in self.all_names

    def __getitem__(self, name) -> Optional[str]:
        try:
            return self.names_to_packages[name]
        except KeyError:
            if name in self.type_defs:
                return None
            else:
                raise KeyError(name)

    def __len__(self):
        return len(self.all_names)


class ImportStrategy(Enum):
    USE_EXISTING = auto()  # don't add any import, strip dotted path from docstring type
    USE_EXISTING_DOTTED = auto()  # don't add any import
    ADD_FROM = auto()  # from <dotted.package.path> import <name list>
    ADD_DOTTED = auto()  # import <dotted.package.path>


DOTTED_PATH_STRATEGIES: Final = {
    ImportStrategy.ADD_DOTTED,
    ImportStrategy.USE_EXISTING_DOTTED,
}


class AmbiguousTypeError(Exception):
    settings = inject.attr("settings")

    @property
    def should_fail(self):
        return self.settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.FAIL


class ModuleHasStarImportError(AmbiguousTypeError):
    pass


class NameMatchesRelativeImportError(AmbiguousTypeError):
    pass


class NameMatchesLocalClassError(AmbiguousTypeError):
    pass


class NotFoundNoPathError(AmbiguousTypeError):
    @property
    def should_fail(self):
        return self.settings.UNPATHED_TYPE_POLICY is UnpathedTypePolicy.FAIL


class ImportCollisionPolicy(Enum):
    IMPORT = auto()  # annotate and add an import, no warning
    NO_IMPORT = auto()  # annotate but don't add import, show warning
    FAIL = auto()  # don't annotate, show error


class UnpathedTypePolicy(Enum):
    IGNORE = auto()  # annotate as documented (may not work), no warning
    WARN = auto()  # annotate as documented (may not work), show warning
    FAIL = auto()  # don't annotate, show error


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    DISABLED = logging.ERROR + 100


LOG_LEVEL_LABELS: Final = {
    LogLevel.DEBUG: "debug",
    LogLevel.INFO: "info",
    LogLevel.WARNING: "warning",
    LogLevel.ERROR: "error",
}


PRINTABLE_SETTINGS: Final = {
    "PYTHON_VERSION",
    "ALLOW_UNTYPED_ARGS",
    "REQUIRE_RETURN_TYPE",
    "IMPORT_COLLISION_POLICY",
    "UNPATHED_TYPE_POLICY",
}
