from typing import Dict, Tuple

from hypothesis import strategies as st

from tests.refactor.types import (
    Ambiguity,
    AmbiguousImport,
    DocType,
    ImportT,
    ImportType,
    NoImport,
    NonAmbiguousImport,
    TypeDef,
    TypeSrc,
)


docstring_type = st.sampled_from([
    DocType(
        'SomeClass',
        {'SomeClass': (TypeDef.BARE_NAME, TypeSrc.USER)},
        {},
    ),
    DocType(
        'my.module.SomeClass',
        {'my.module.SomeClass': (TypeDef.DOTTED_PATH, TypeSrc.USER)},
        {'my.module.SomeClass': ('my.module', 'SomeClass')},
    ),
    DocType(
        'Callable[[SomeClass], bool]',
        {
            'SomeClass': (TypeDef.BARE_NAME, TypeSrc.USER),
            'Callable': (TypeDef.BARE_NAME, TypeSrc.TYPING),
            'bool': (TypeDef.BARE_NAME, TypeSrc.BUILTINS),
        },
        {'Callable': ('typing', 'Callable')},
    ),
    DocType(
        'Callable[[int], SomeClass]',
        {
            'SomeClass': (TypeDef.BARE_NAME, TypeSrc.USER),
            'Callable': (TypeDef.BARE_NAME, TypeSrc.TYPING),
            'int': (TypeDef.BARE_NAME, TypeSrc.BUILTINS),
        },
        {'Callable': ('typing', 'Callable')},
    ),
    DocType(
        'Callable[[my.module.SomeClass], bool]',
        {
            'my.module.SomeClass': (TypeDef.DOTTED_PATH, TypeSrc.USER),
            'Callable': (TypeDef.BARE_NAME, TypeSrc.TYPING),
            'bool': (TypeDef.BARE_NAME, TypeSrc.BUILTINS),
        },
        {
            'Callable': ('typing', 'Callable'),
            'my.module.SomeClass': ('my.module', 'SomeClass'),
        },
    ),
    DocType(
        'Tuple[SomeClass, ...]',
        {
            'SomeClass': (TypeDef.BARE_NAME, TypeSrc.USER),
            'Tuple': (TypeDef.BARE_NAME, TypeSrc.TYPING),
            '...': (TypeDef.BARE_NAME, TypeSrc.NON_TYPE),
        },
        {'Tuple': ('typing', 'Tuple')},
    ),
    DocType(
        'typing.Tuple[SomeClass, ...]',
        {
            'SomeClass': (TypeDef.BARE_NAME, TypeSrc.USER),
            'typing.Tuple': (TypeDef.DOTTED_PATH, TypeSrc.TYPING),
            '...': (TypeDef.BARE_NAME, TypeSrc.NON_TYPE),
        },
        {'typing.Tuple': ('typing', 'Tuple')},
    ),
])


@st.composite
def SomeClass_import_f(draw, type_def: TypeDef) -> ImportT:
    imports = (
        NoImport.MISSING,
        NoImport.LOCAL_CLS,
        NonAmbiguousImport(
            'from my.module import SomeClass', ImportType.FROM_PKG_IMPORT_NAME
        ),
        NonAmbiguousImport(
            'from my.module import OtherClass, SomeClass, AnotherClass', ImportType.FROM_PKG_IMPORT_NAME
        ),
        NonAmbiguousImport(
            """from my.module import (
    OtherClass,
    SomeClass,
    AnotherClass,
)""",
            ImportType.FROM_PKG_IMPORT_NAME
        ),
    )
    if type_def is TypeDef.DOTTED_PATH:
        imports += (
            NonAmbiguousImport(
                'import my.module', ImportType.PACKAGE_ONLY
            ),
            AmbiguousImport(
                'from my.module import *', Ambiguity.STAR_IMPORT
            ),
            AmbiguousImport(
                'from other.module import SomeClass', Ambiguity.NAME_CLASH
            ),
            AmbiguousImport(
                'from .. import SomeClass', Ambiguity.RELATIVE_IMPORT
            ),
        )
    return draw(st.sampled_from(imports))


@st.composite
def typing_import_f(draw, type_def: TypeDef) -> ImportT:
    imports = (
        NoImport.MISSING,
        NonAmbiguousImport(
            'from typing import Callable, Tuple', ImportType.FROM_PKG_IMPORT_NAME
        ),
        NonAmbiguousImport(
            'from typing import Callable, Set, Tuple', ImportType.FROM_PKG_IMPORT_NAME
        ),
        NonAmbiguousImport(
            """from typing import (
    Callable,
    Set,
    Tuple,
)""",
            ImportType.FROM_PKG_IMPORT_NAME
        ),
    )
    if type_def is TypeDef.DOTTED_PATH:
        imports += (
            NonAmbiguousImport(
                'import typing', ImportType.PACKAGE_ONLY
            ),
            AmbiguousImport(
                'from typing import *', Ambiguity.STAR_IMPORT
            ),
            AmbiguousImport(
                'from other.module import Callable, Tuple', Ambiguity.NAME_CLASH
            ),
            AmbiguousImport(
                'from .. import Callable, Tuple', Ambiguity.RELATIVE_IMPORT
            ),
        )
    return draw(st.sampled_from(imports))


@st.composite
def type_and_imports_f(draw) -> Tuple[DocType, Dict[str, ImportT]]:
    arg_type = draw(docstring_type)
    import_statements = {}
    for type_name, (type_def, type_src) in arg_type.type_map.items():
        if type_src is TypeSrc.USER:
            import_statements[type_name] = draw(SomeClass_import_f(type_def))
        elif type_src is TypeSrc.TYPING:
            import_statements[type_name] = draw(typing_import_f(type_def))
        else:
            # builtin / non-type
            import_statements[type_name] = NoImport.NOT_NEEDED
    return arg_type, import_statements
