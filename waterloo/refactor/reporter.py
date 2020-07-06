from enum import Enum
from functools import singledispatch

import inject
import parsy
from fissix.pytree import Leaf

from waterloo.types import (
    PRINTABLE_SETTINGS,
    AmbiguousTypeError,
    ImportCollisionPolicy,
    ModuleHasStarImportError,
    NameMatchesLocalClassError,
    NameMatchesRelativeImportError,
    NotFoundNoPathError,
    UnpathedTypePolicy,
)


@inject.params(settings="settings", echo="echo")
def report_settings(settings, echo):
    echo.debug("Running with options:", verbose=True)
    for key in sorted(PRINTABLE_SETTINGS):
        try:
            val = getattr(settings, key)
        except AttributeError:
            continue
        if isinstance(val, Enum):
            echo.debug(f"- {key}: <b>{val.name}</b>", verbose=True)
        elif isinstance(val, str):
            echo.debug(f"- {key}: <b>{val!r}</b>", verbose=True)
        else:
            echo.debug(f"- {key}: <b>{val}</b>", verbose=True)
    echo.debug("", verbose=True)


@inject.params(echo="echo", log="log", threadlocals="threadlocals")
def report_parse_error(e: parsy.ParseError, function: Leaf, echo, log, threadlocals):
    threadlocals.error_count += 1
    # fmt: off
    log.error(
        "Error parsing docstring.",
        line_no=function.lineno,
        func_name=function.value,
        error=e,
    )
    echo.error(
        f"🛑 <b>line {function.lineno}:</b> Error parsing docstring for <b>def {function.value}</b>\n"
        f"   {e!r}",
        verbose=True
    )
    # fmt: on


@inject.params(echo="echo", log="log", threadlocals="threadlocals")
def report_doc_args_signature_mismatch_error(function: Leaf, echo, log, threadlocals):
    threadlocals.error_count += 1
    # fmt: off
    log.error(
        "Docstring has arg names which are inconsistent with the function signature.",
        line_no=function.lineno,
        func_name=function.value,
    )
    msg = (
        f"<b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> has arg names which are "
        f"inconsistent with the function signature."
    )
    echo.error(
        f"🛑 {msg}\n"
        f"   ➤ no type annotation added",
        verbose=True
    )
    # fmt: on


@inject.params(settings="settings", echo="echo", log="log", threadlocals="threadlocals")
def report_incomplete_arg_types(function: Leaf, settings, echo, log, threadlocals):
    # fmt: off
    msg = f"<b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not fully specify arg types."
    if not settings.ALLOW_UNTYPED_ARGS:
        threadlocals.error_count += 1
        log.error(
            "Docstring did not fully specify arg types: no type annotation added.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added",
            verbose=True
        )
    else:
        threadlocals.warning_count += 1
        log.warning(
            "Docstring did not fully specify arg types: args will be annotated as (...)",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ args will be annotated as <b>(...)</b>",
            verbose=True
        )
    # fmt: on


@inject.params(settings="settings", echo="echo", log="log", threadlocals="threadlocals")
def report_incomplete_return_type(function: Leaf, settings, echo, log, threadlocals):
    # fmt: off
    msg = f"<b>line {function.lineno}:</b> Docstring for <b>def {function.value}</b> did not specify a return type."
    if settings.REQUIRE_RETURN_TYPE:
        threadlocals.error_count += 1
        log.error(
            "Docstring did not specify a return type: no type annotation added.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added",
            verbose=True
        )
    else:
        threadlocals.warning_count += 1
        log.warning(
            "Docstring did not specify a return type: return will be annotated as -> None",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ return will be annotated as <b>-&gt; None</b>",
            verbose=True
        )
    # fmt: on


@inject.params(threadlocals="threadlocals")
@singledispatch
def report_ambiguous_type_error(e: AmbiguousTypeError, function: Leaf, threadlocals):
    threadlocals.error_count += 1
    # fmt: off
    raise TypeError(
        f"Unexpected AmbiguousTypeError: {e!r}"
    )
    # fmt: on


@report_ambiguous_type_error.register
@inject.params(settings="settings", echo="echo", log="log", threadlocals="threadlocals")
def _(e: ModuleHasStarImportError, function: Leaf, settings, echo, log, threadlocals):
    t_module, t_name = e.args
    assert t_module
    # fmt: off
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{t_module}.{t_name}</b> in docstring for <b>def {function.value}</b> "
        f"matches \"from {t_module} import *\" but we don't know if \"{t_name}\" is in *."
    )
    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.NO_IMPORT:
        threadlocals.warning_count += 1
        log.warning(
            f"Ambiguous Type: {t_module}.{t_name} matches \"from {t_module} import *\" but we don't know if \"{t_name}\" is in *. "
            f"Annotation added: assumes existing import is sufficient.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume existing import is sufficient\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with ImportCollisionPolicy.IMPORT",
            verbose=True
        )
    elif e.should_fail:
        threadlocals.error_count += 1
        log.error(
            f"Ambiguous Type: {t_module}.{t_name} matches \"from {t_module} import *\" but we don't know if \"{t_name}\" is in *. "
            f"No type annotation added.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with ImportCollisionPolicy.IMPORT",
            verbose=True
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"IMPORT_COLLISION_POLICY={settings.IMPORT_COLLISION_POLICY.name}"
        )
    # fmt: on


@report_ambiguous_type_error.register
@inject.params(settings="settings", echo="echo", log="log", threadlocals="threadlocals")
def _(e: NameMatchesLocalClassError, function: Leaf, settings, echo, log, threadlocals):
    t_module, t_name = e.args
    type_path = f"{t_module}.{t_name}" if t_module else t_name
    # fmt: off
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{type_path}</b> in docstring for <b>def {function.value}</b> "
        f"matches a \"class {t_name}\" also defined in the module, but we don't know if it is the same."
    )
    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.NO_IMPORT:
        threadlocals.warning_count += 1
        log.warning(
            f"Ambiguous Type: {type_path} matches a \"class {t_name}\" also defined in the module, "
            f"but we don't know if it is the same. Annotation added: assumes it was intended to match local class def.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume was intended to match local class def\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with ImportCollisionPolicy.IMPORT",
            verbose=True
        )
    elif e.should_fail:
        threadlocals.error_count += 1
        log.error(
            f"Ambiguous Type: {type_path} matches a \"class {t_name}\" also defined in the module, "
            f"but we don't know if it is the same. No type annotation added.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with ImportCollisionPolicy.IMPORT",
            verbose=True
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"IMPORT_COLLISION_POLICY={settings.IMPORT_COLLISION_POLICY.name}"
        )
    # fmt: on


@report_ambiguous_type_error.register
@inject.params(settings="settings", echo="echo", log="log", threadlocals="threadlocals")
def _(
    e: NameMatchesRelativeImportError, function: Leaf, settings, echo, log, threadlocals
):
    t_module, t_name = e.args
    type_path = f"{t_module}.{t_name}" if t_module else t_name
    # fmt: off
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{type_path}</b> in docstring for <b>def {function.value}</b> "
        f"matches a \"{t_name}\" imported from a relative path, but we don't know if it is the same."
    )
    if settings.IMPORT_COLLISION_POLICY is ImportCollisionPolicy.NO_IMPORT:
        threadlocals.warning_count += 1
        log.warning(
            f"Ambiguous Type: {type_path} matches a \"{t_name}\" imported from a relative path, "
            f"but we don't know if it is the same. Annotation added: assumes existing import is sufficient.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume existing import is sufficient\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with ImportCollisionPolicy.IMPORT",
            verbose=True
        )
    elif e.should_fail:
        threadlocals.error_count += 1
        log.error(
            f"Ambiguous Type: {type_path} matches a \"{t_name}\" imported from a relative path, "
            f"but we don't know if it is the same. No type annotation added.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with ImportCollisionPolicy.IMPORT",
            verbose=True
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"IMPORT_COLLISION_POLICY={settings.IMPORT_COLLISION_POLICY.name}"
        )
    # fmt: on


@report_ambiguous_type_error.register
@inject.params(settings="settings", echo="echo", log="log", threadlocals="threadlocals")
def _(e: NotFoundNoPathError, function: Leaf, settings, echo, log, threadlocals):
    _, t_name = e.args
    # fmt: off
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{t_name}</b> in docstring for <b>def {function.value}</b> "
        f"does not match any builtins, typing.&lt;Type&gt;, imported names or class def in the file, and does not provide "
        f"a dotted-path we can use to add an import statement. However there are some forms we cannot auto-detect "
        f"which may mean no import is needed."
    )
    if settings.UNPATHED_TYPE_POLICY in {UnpathedTypePolicy.WARN, UnpathedTypePolicy.IGNORE}:
        threadlocals.warning_count += 1
        log.warning(
            f"Ambiguous Type: {t_name} does not match any builtins, typing.<Type>, imported names or class def in the file, "
            f"and does not provide a dotted-path we can use to add an import statement. Annotation added: assumes no import needed.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume no import needed",
            verbose=True
        )
    elif e.should_fail:
        threadlocals.error_count += 1
        log.error(
            f"Ambiguous Type: {t_name} does not match any builtins, typing.<Type>, imported names or class def in the file, "
            f"and does not provide a dotted-path we can use to add an import statement. No type annotation added.",
            line_no=function.lineno,
            func_name=function.value,
        )
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an annotation to be added (without accompanying import), re-run with UnpathedTypePolicy.WARN|IGNORE",
            verbose=True
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"UNPATHED_TYPE_POLICY={settings.UNPATHED_TYPE_POLICY.name}"
        )
    # fmt: on


@inject.params(settings="settings", echo="echo", log="log", threadlocals="threadlocals")
def report_generator_annotation(function: Leaf, settings, echo, log, threadlocals):
    threadlocals.warning_count += 1
    log.warning(
        "Docstring contains a Yields section. We have annotated this as -> Generator[<yield type>, None, None]. "
        "If you also make use of a SendType and/or ReturnType then you will need to manually update this annotation.",
        line_no=function.lineno,
        func_name=function.value,
    )
    msg = (
        f"Function yields: <b>def {function.value}</b> docstring contains a Yields section. We have annotated "
        f"this as <b>-&gt; Generator[&lt;yield type&gt;, None, None]</b>. If you make use of a SendType and/or ReturnType then "
        f"you will need to manually update this annotation."
    )
    echo.warning(
        f"⚠️  {msg}\n" f"   ➤ annotation added: check if Generator type is correct",
        verbose=True,
    )
