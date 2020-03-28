from enum import Enum
from functools import singledispatch

import inject
import parsy
from fissix.pytree import Leaf

from waterloo.types import (
    AmbiguousTypeError,
    ImportCollisionPolicy,
    ModuleHasStarImportError,
    NameMatchesLocalClassError,
    NameMatchesRelativeImportError,
    NotFoundNoPathError,
    PRINTABLE_SETTINGS,
    UnpathedTypePolicy,
)


@inject.params(settings='settings', echo='echo')
def report_settings(settings, echo):
    for key in sorted(PRINTABLE_SETTINGS):
        try:
            val = getattr(settings, key)
        except AttributeError:
            continue
        if isinstance(val, Enum):
            echo.debug(f"- {key}: <b>{val.name}</b>")
        elif isinstance(val, str):
            echo.debug(f"- {key}: <b>{val!r}</b>")
        else:
            echo.debug(f"- {key}: <b>{val}</b>")
    echo.debug("")


@inject.params(echo='echo')
def report_parse_error(e: parsy.ParseError, function: Leaf, echo):
    echo.error(
        f"🛑 <b>line {function.lineno}:</b> Error parsing docstring for <b>def {function.value}</b>\n"
        f"   {e!r}"
    )


@inject.params(settings='settings', echo='echo')
def report_incomplete_arg_types(function: Leaf, settings, echo):
    msg = f"<b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not fully specify arg types."
    if not settings.ALLOW_UNTYPED_ARGS:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added"
        )
    else:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ args will be annotated as <b>(...)</b>"
        )


@inject.params(settings='settings', echo='echo')
def report_incomplete_return_type(function: Leaf, settings, echo):
    msg = f"<b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not specify a return type."
    if settings.REQUIRE_RETURN_TYPE:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added"
        )
    else:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ return will be annotated as <b>-> None</b>"
        )


@singledispatch
def report_ambiguous_type_error(
    e: AmbiguousTypeError,
    function: Leaf,
):
    raise TypeError(
        f"Unexpected AmbiguousTypeError: {e!r}"
    )


@report_ambiguous_type_error.register
@inject.params(settings='settings', echo='echo')
def _(
    e: ModuleHasStarImportError,
    function: Leaf,
    settings,
    echo,
):
    t_module, t_name = e.args
    assert t_module
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{t_module}.{t_name}</b> in docstring for <b>def {function.value}</b> "
        f"matches \"from {t_module} import *\" but we don't know if \"{t_name}\" is in *."
    )
    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.NO_IMPORT:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume existing import is sufficient\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with ImportCollisionPolicy.IMPORT"
        )
    elif e.should_fail:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with ImportCollisionPolicy.IMPORT"
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"IMPORT_COLLISION_POLICY={settings.IMPORT_COLLISION_POLICY.name}"
        )


@report_ambiguous_type_error.register
@inject.params(settings='settings', echo='echo')
def _(
    e: NameMatchesLocalClassError,
    function: Leaf,
    settings,
    echo,
):
    t_module, t_name = e.args
    type_path = f"{t_module}.{t_name}" if t_module else t_name
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{type_path}</b> in docstring for <b>def {function.value}</b> "
        f"matches a \"class {t_name}\" also defined in the module, but we don't know if it is the same."
    )
    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.NO_IMPORT:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume was intended to match local class def\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with ImportCollisionPolicy.IMPORT"
        )
    elif e.should_fail:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with ImportCollisionPolicy.IMPORT"
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"IMPORT_COLLISION_POLICY={settings.IMPORT_COLLISION_POLICY.name}"
        )


@report_ambiguous_type_error.register
@inject.params(settings='settings', echo='echo')
def _(
    e: NameMatchesRelativeImportError,
    function: Leaf,
    settings,
    echo,
):
    t_module, t_name = e.args
    type_path = f"{t_module}.{t_name}" if t_module else t_name
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{type_path}</b> in docstring for <b>def {function.value}</b> "
        f"matches a \"{t_name}\" imported from a relative path, but we don't know if it is the same."
    )
    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.NO_IMPORT:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume existing import is sufficient\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with ImportCollisionPolicy.IMPORT"
        )
    elif e.should_fail:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with ImportCollisionPolicy.IMPORT"
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"IMPORT_COLLISION_POLICY={settings.IMPORT_COLLISION_POLICY.name}"
        )


@report_ambiguous_type_error.register
@inject.params(settings='settings', echo='echo')
def _(
    e: NotFoundNoPathError,
    function: Leaf,
    settings,
    echo,
):
    _, t_name = e.args
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{t_name}</b> in docstring for <b>def {function.value}</b> "
        f"does not match any builtins, typing.&lt;Type&gt;, imported names or class def in the file, and does not provide "
        f"a dotted-path we can use to add an import statement. However there are some forms we cannot auto-detect "
        f"which may mean no import is needed."
    )
    if settings.UNPATHED_TYPE_POLICY in {UnpathedTypePolicy.WARN, UnpathedTypePolicy.IGNORE}:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume no import needed"
        )
    elif e.should_fail:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an annotation to be added (without accompanying import), re-run with UnpathedTypePolicy.WARN|IGNORE"
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"UNPATHED_TYPE_POLICY={settings.UNPATHED_TYPE_POLICY.name}"
        )
