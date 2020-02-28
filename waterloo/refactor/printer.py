from typing import Set

import parsy
from bowler import Capture

from waterloo.conf import settings
from waterloo.types import (
    AmbiguousTypePolicy,
    ModuleHasStarImportError,
    NameMatchesRelativeImportError,
    NotFoundNoPathError,
)
from waterloo.utils import StylePrinter


echo = StylePrinter(getattr(settings, 'ECHO_STYLES', None))


def report_parse_error(function: Capture, e: parsy.ParseError):
    echo.error(
        f"🛑 <b>line {function.lineno}:</b> Error parsing docstring for <b>def {function.value}</b>\n"
        f"   {e!r}"
    )


def report_incomplete_arg_types(function: Capture):
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


def report_incomplete_return_type(function: Capture):
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


def report_module_has_star_import(
    function: Capture,
    e: ModuleHasStarImportError,
    fail_policies: Set[AmbiguousTypePolicy],
):
    t_module, t_name = e.args
    assert t_module
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{t_module}.{t_name}</b> in docstring for <b>def {function.value}</b> "
        f"matches \"from {t_module} import *\" but we don't know if \"{t_name}\" is in *."
    )
    if settings.AMBIGUOUS_TYPE_POLICY is AmbiguousTypePolicy.WARN:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume existing import is sufficient\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with AmbiguousTypePolicy.AUTO"
        )
    elif settings.AMBIGUOUS_TYPE_POLICY in fail_policies:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with AmbiguousTypePolicy.AUTO"
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"AMBIGUOUS_TYPE_POLICY={settings.AMBIGUOUS_TYPE_POLICY.name}"
        )


def report_name_matches_relative_import(
    function: Capture,
    e: NameMatchesRelativeImportError,
    fail_policies: Set[AmbiguousTypePolicy],
):
    t_module, t_name = e.args
    type_path = f"{t_module}.{t_name}" if t_module else t_name
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{type_path}</b> in docstring for <b>def {function.value}</b> "
        f"matches a \"{t_name}\" imported from a relative path, but we don't know if it is the same."
    )
    if settings.AMBIGUOUS_TYPE_POLICY is AmbiguousTypePolicy.WARN:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume existing import is sufficient\n"
            f"   ➤ if you would like a specific import to be added, undo this change and re-run with AmbiguousTypePolicy.AUTO"
        )
    elif settings.AMBIGUOUS_TYPE_POLICY in fail_policies:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an import and annotation to be added, re-run with AmbiguousTypePolicy.AUTO"
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"AMBIGUOUS_TYPE_POLICY={settings.AMBIGUOUS_TYPE_POLICY.name}"
        )


def report_not_found_no_path(
    function: Capture,
    e: NotFoundNoPathError,
    fail_policies: Set[AmbiguousTypePolicy],
):
    _, t_name = e.args
    msg = (
        f"<b>line {function.lineno}:</b> Ambiguous Type: <b>{t_name}</b> in docstring for <b>def {function.value}</b> "
        f"does not match any builtins, typing.&lt;Type&gt;, imported names or class def in the file, and does not provide "
        f"a dotted-path we can use to add an import statement. However there are some forms we cannot auto-detect "
        f"which may mean no import is needed."
    )
    if settings.AMBIGUOUS_TYPE_POLICY is AmbiguousTypePolicy.WARN:
        echo.warning(
            f"⚠️  {msg}\n"
            f"   ➤ annotation added: will assume no import needed"
        )
    elif settings.AMBIGUOUS_TYPE_POLICY in fail_policies:
        echo.error(
            f"🛑 {msg}\n"
            f"   ➤ no type annotation added\n"
            f"   ➤ if you would like an annotation to be added (without auto-added import), re-run with AmbiguousTypePolicy.WARN"
        )
    else:
        raise ValueError(
            f"Unexpected fall-thru for {e.__class__.__name__} and "
            f"AMBIGUOUS_TYPE_POLICY={settings.AMBIGUOUS_TYPE_POLICY.name}"
        )
