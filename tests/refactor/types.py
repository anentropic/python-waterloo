from enum import Enum, auto
from typing import Dict, NamedTuple, Tuple, Union
from typing_extensions import Final


class TypeDef(Enum):
    BARE_NAME = auto()
    DOTTED_PATH = auto()


class TypeSrc(Enum):
    USER = auto()
    TYPING = auto()
    BUILTINS = auto()
    NON_TYPE = auto()


MAY_NEED_IMPORT: Final = {TypeSrc.USER, TypeSrc.TYPING}


class Ambiguity(Enum):
    NAME_CLASH = auto()
    RELATIVE_IMPORT = auto()
    STAR_IMPORT = auto()


class NoImport(Enum):
    MISSING = auto()
    LOCAL_CLS = auto()
    NOT_NEEDED = auto()


class ImportType(Enum):
    PACKAGE_ONLY = auto()
    FROM_PKG_IMPORT_NAME = auto()


class DocType(NamedTuple):
    type_def: str
    type_map: Dict[str, Tuple[TypeDef, TypeSrc]]
    import_map: Dict[str, Tuple[str, str]]


class NonAmbiguousImport(NamedTuple):
    import_statement: str
    import_type: ImportType


class AmbiguousImport(NamedTuple):
    import_statement: str
    ambiguity: Ambiguity


ImportT = Union[NonAmbiguousImport, AmbiguousImport, NoImport]
