import tempfile
from typing import Dict, Tuple

import inject
from hypothesis import given, note, strategies as st

from tests.refactor import strategies
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
from waterloo import configuration_factory
from waterloo.parsers.napoleon import type_atom
from waterloo.refactor.annotations import annotate
from waterloo.types import ImportCollisionPolicy, ImportStrategy, UnpathedTypePolicy


"""
We can assume that docstring parsing is already well-tested.

Cases to test:
- has fully typed args & return in docstring:
  - for each arg/return type:
    - (dotted or unpathed) matching import or classdef as:
      - top-level name
      - conditional top-level name (assume condition is evaluated, arbitrary nesting)
      - nested name, in-scope
      - nested name, out-of-scope (current code does not discriminate)
      - type has dotted path and a matching `import <package>` is found
    - (dotted only) ambiguous import:
      - same name, different package
      - same name, relative import package (effectively same as above)
      - star import, same package
    - (dotted or unpathed) no matching import:
      - name is a builtin
      - none of the above:
        - has dotted path -> import should be added
        - no dotted path -> if UNPATHED_TYPE_POLICY, error
- has fully typed args, no return:
  - for each arg as above
  - REQUIRE_RETURN_TYPE on/off
- has incomplete args, typed return:
  - for return type as above
  - ALLOW_UNTYPED_ARGS on/off
- non-Napoleon docstring / no types
- py2 / py3 syntax
- content before first import statement:
  - module docstring
  - shebang
  - comment
  - blank lines
  - nothing
"""


@given(
    import_collision_policy=st.sampled_from(ImportCollisionPolicy),
    unpathed_type_policy=st.sampled_from(UnpathedTypePolicy),
    type_and_imports=strategies.type_and_imports_f(),
)
@inject.params(settings="settings")
def test_fully_typed(
    import_collision_policy: ImportCollisionPolicy,
    unpathed_type_policy: UnpathedTypePolicy,
    type_and_imports: Tuple[DocType, Dict[str, ImportT]],
    settings,
):
    (type_name, type_map, import_map), imports = type_and_imports
    note(f"{type_and_imports}")
    note(f"import_collision_policy: {import_collision_policy}")
    note(f"unpathed_type_policy: {unpathed_type_policy}")
    assert type_map.keys() >= imports.keys()

    expect_annotated = True
    expected_import_strategy = {}
    class_defs_needed = set()
    for name, import_t in imports.items():
        type_def, type_src = type_map[name]
        if isinstance(import_t, NonAmbiguousImport):
            if import_t.import_type is ImportType.FROM_PKG_IMPORT_NAME:
                expected_import_strategy[name] = ImportStrategy.USE_EXISTING
            elif import_t.import_type is ImportType.PACKAGE_ONLY:
                expected_import_strategy[name] = ImportStrategy.USE_EXISTING_DOTTED
            else:
                raise TypeError(import_t.import_type)
        elif isinstance(import_t, AmbiguousImport):
            if import_t.ambiguity is Ambiguity.NAME_CLASH:
                expected_import_strategy[name] = ImportStrategy.ADD_DOTTED
            else:
                if import_collision_policy is ImportCollisionPolicy.FAIL:
                    expect_annotated = False
                elif import_collision_policy is ImportCollisionPolicy.IMPORT:
                    if import_t.ambiguity is Ambiguity.STAR_IMPORT:
                        expected_import_strategy[name] = ImportStrategy.ADD_FROM
                    elif import_t.ambiguity is Ambiguity.RELATIVE_IMPORT:
                        expected_import_strategy[name] = ImportStrategy.ADD_DOTTED
                    else:
                        raise TypeError(import_t.ambiguity)
                else:
                    expected_import_strategy[name] = ImportStrategy.USE_EXISTING
        elif isinstance(import_t, NoImport):
            if import_t is NoImport.NOT_NEEDED:
                expected_import_strategy[name] = ImportStrategy.USE_EXISTING
            elif import_t is NoImport.LOCAL_CLS:
                if type_def is TypeDef.DOTTED_PATH:
                    if import_collision_policy is ImportCollisionPolicy.FAIL:
                        expect_annotated = False
                    expected_import_strategy[name] = (
                        ImportStrategy.ADD_DOTTED
                        if import_collision_policy is ImportCollisionPolicy.IMPORT
                        else ImportStrategy.USE_EXISTING
                    )
                else:
                    expected_import_strategy[name] = ImportStrategy.USE_EXISTING
                class_defs_needed.add(name.rsplit(".", 1)[-1])
            elif import_t is NoImport.MISSING:
                if type_def is TypeDef.DOTTED_PATH:
                    expected_import_strategy[name] = ImportStrategy.ADD_FROM
                elif type_src is TypeSrc.TYPING:
                    expected_import_strategy[name] = ImportStrategy.ADD_FROM
                elif type_src is TypeSrc.USER:
                    if unpathed_type_policy is UnpathedTypePolicy.FAIL:
                        expect_annotated = False
                    expected_import_strategy[name] = ImportStrategy.USE_EXISTING
                else:
                    # builtin / non-type
                    expected_import_strategy[name] = ImportStrategy.USE_EXISTING
            else:
                raise TypeError(import_t)
        else:
            raise TypeError(import_t)

    note(f"expect_annotated: {expect_annotated}")
    note(f"expected_import_strategy: {expected_import_strategy}")

    import_lines = "\n".join(
        i.import_statement for i in imports.values() if not isinstance(i, NoImport)
    )

    class_defs = "\n\n\n".join(
        f"""
class {cls_name}(object):
    pass"""
        for cls_name in class_defs_needed
    )

    funcdef = f'''
def identity(arg1):
    """
    Args:
        arg1 ({type_name}): blah

    Returns:
        {type_name}: blah
    """
    return arg1
'''

    content = "\n\n".join(var for var in (import_lines, class_defs, funcdef) if var)
    note(content)

    NO_ADD_STRATEGIES = {
        ImportStrategy.USE_EXISTING,
        ImportStrategy.USE_EXISTING_DOTTED,
    }
    if expect_annotated:
        # add imports expected to have been added
        imports_to_add = []
        for name, strategy in expected_import_strategy.items():
            if strategy in NO_ADD_STRATEGIES:
                continue
            package, module = import_map[name]
            if strategy is ImportStrategy.ADD_FROM:
                imports_to_add.append(f"from {package} import {module}")
            elif strategy is ImportStrategy.ADD_DOTTED:
                imports_to_add.append(f"import {package}")

        atom = type_atom.parse(type_name)
        annotated_type_name = atom.to_annotation(expected_import_strategy)

        added_imports = "\n".join(imports_to_add)
    else:
        added_imports = ""

    if expect_annotated:
        funcdef = f'''
def identity(arg1):
    # type: ({annotated_type_name}) -> {annotated_type_name}
    """
    Args:
        arg1: blah

    Returns:
        blah
    """
    return arg1
'''

    if added_imports:
        if import_lines:
            import_lines = f"{import_lines}\n{added_imports}"
        else:
            import_lines = added_imports

    expected = "\n\n".join(var for var in (import_lines, class_defs, funcdef) if var)
    note(expected)

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = settings.copy(deep=True)
        test_settings.ALLOW_UNTYPED_ARGS = False
        test_settings.REQUIRE_RETURN_TYPE = False
        test_settings.IMPORT_COLLISION_POLICY = import_collision_policy
        test_settings.UNPATHED_TYPE_POLICY = unpathed_type_policy

        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected
