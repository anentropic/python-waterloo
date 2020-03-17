import tempfile

import inject
import pytest

from waterloo import configuration_factory
from waterloo.refactor.annotations import annotate
from waterloo.types import (
    ImportCollisionPolicy,
    UnpathedTypePolicy,
)


@pytest.mark.parametrize('allow_untyped_args', [
    True,
    False
])
@inject.params(settings='settings')
def test_allow_untyped_args(allow_untyped_args, settings=None):
    content = '''
def identity(arg1):
    """
    Args:
        arg1: blah

    Returns:
        Tuple[str, ...]: blah
    """
    return arg1
'''

    if allow_untyped_args:
        expected = '''from typing import Tuple


def identity(arg1):
    # type: (...) -> Tuple[str, ...]
    """
    Args:
        arg1: blah

    Returns:
        blah
    """
    return arg1
'''
    else:
        expected = content

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = settings.copy(deep=True)
        test_settings.ALLOW_UNTYPED_ARGS = allow_untyped_args
        test_settings.REQUIRE_RETURN_TYPE = False
        test_settings.IMPORT_COLLISION_POLICY = ImportCollisionPolicy.IMPORT
        test_settings.UNPATHED_TYPE_POLICY = UnpathedTypePolicy.FAIL

        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name,
            in_process=True,
            interactive=False,
            write=True,
            silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


@pytest.mark.parametrize('require_return_type', [
    True,
    False
])
@inject.params(settings='settings')
def test_require_return_type(require_return_type, settings=None):
    content = '''
def identity(arg1):
    """
    Args:
        arg1 (Tuple[str, ...]): blah
    """
    return arg1
'''

    if not require_return_type:
        expected = '''from typing import Tuple


def identity(arg1):
    # type: (Tuple[str, ...]) -> None
    """
    Args:
        arg1: blah
    """
    return arg1
'''
    else:
        expected = content

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = settings.copy(deep=True)
        test_settings.ALLOW_UNTYPED_ARGS = False
        test_settings.REQUIRE_RETURN_TYPE = require_return_type
        test_settings.IMPORT_COLLISION_POLICY = ImportCollisionPolicy.IMPORT
        test_settings.UNPATHED_TYPE_POLICY = UnpathedTypePolicy.FAIL

        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name,
            in_process=True,
            interactive=False,
            write=True,
            silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected
