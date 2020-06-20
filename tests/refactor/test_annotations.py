import tempfile

import inject
import pytest

from tests.utils import override_settings
from waterloo import configuration_factory
from waterloo.refactor.annotations import annotate
from waterloo.types import ImportCollisionPolicy, UnpathedTypePolicy


@pytest.mark.parametrize("allow_untyped_args", [True, False])
def test_allow_untyped_args(allow_untyped_args):
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

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=allow_untyped_args,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


@pytest.mark.parametrize("allow_untyped_args", [True, False])
def test_allow_missing_args_section_single_arg(allow_untyped_args):
    content = '''
def identity(arg1):
    """
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

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=allow_untyped_args,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


@pytest.mark.parametrize("allow_untyped_args", [True, False])
def test_allow_missing_args_section_multiple_args(allow_untyped_args):
    content = '''
def identity(arg1, *args, **kwargs):
    """
    Returns:
        Tuple[str, ...]: blah
    """
    return arg1
'''

    if allow_untyped_args:
        expected = '''from typing import Tuple


def identity(arg1, *args, **kwargs):
    # type: (...) -> Tuple[str, ...]
    """
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

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=allow_untyped_args,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


@pytest.mark.parametrize("allow_untyped_args", [True, False])
def test_allow_missing_args_section_no_args_func(allow_untyped_args):
    """
    If func has no args but 'Returns' is given then we should be
    able to annotate it.
    """
    content = '''
def identity():
    """
    Returns:
        Tuple[str, ...]: blah
    """
    return arg1
'''

    expected = '''from typing import Tuple


def identity():
    # type: () -> Tuple[str, ...]
    """
    Returns:
        blah
    """
    return arg1
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=allow_untyped_args,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


@pytest.mark.parametrize(
    "signature,arg_annotations",
    [
        ("arg1, arg2, arg3", {"arg1": ("int", "blah"), "arg2": ("str", "blah")},),
        (
            "arg1, arg2",
            {
                "arg1": ("int", "blah"),
                "arg2": ("str", "blah"),
                "arg3": ("bool", "blah"),
            },
        ),
        ("arg1, arg2", {"arg1": ("int", "blah"), "arg3": ("str", "blah")},),
    ],
    ids=["missing arg", "extra arg", "name mismatch"],
)
def test_arg_annotation_signature_mismatch(signature, arg_annotations):
    annotations = "\n".join(
        f"        {name} ({type_}): {description}"
        for name, (type_, description) in arg_annotations.items()
    )
    content = f'''
def identity({signature}):
    """
    Args:
{annotations}
    """
    pass
'''

    # in all cases we should not have annotated
    expected = content

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=True,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


@pytest.mark.parametrize("require_return_type", [True, False])
def test_require_return_type(require_return_type):
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

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=require_return_type,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


def test_nested_function():
    content = '''
def outer(arg1):
    """
    Args:
        arg1 (Tuple[str, ...]): blah

    Returns:
        Tuple[my.module.SomeClass[str], ...]: blah
    """
    def inner(arg2):
        """
        Args:
            arg2 (str): blah

        Returns:
            my.module.SomeClass[str]: blah
        """
        return SomeClass(arg2)

    return tuple(
        inner(arg) for arg in arg1
    )
'''

    expected = '''from my.module import SomeClass
from typing import Tuple


def outer(arg1):
    # type: (Tuple[str, ...]) -> Tuple[SomeClass[str], ...]
    """
    Args:
        arg1: blah

    Returns:
        blah
    """
    def inner(arg2):
        # type: (str) -> SomeClass[str]
        """
        Args:
            arg2: blah

        Returns:
            blah
        """
        return SomeClass(arg2)

    return tuple(
        inner(arg) for arg in arg1
    )
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


def test_decorated_function():
    content = '''
@whatever(param=val)
def decorated(arg1):
    """
    Args:
        arg1 (Tuple[str, ...]): blah

    Returns:
        Tuple[int, ...]: blah
    """
    return tuple(
        int(arg) for arg in arg1
    )
'''

    expected = '''from typing import Tuple


@whatever(param=val)
def decorated(arg1):
    # type: (Tuple[str, ...]) -> Tuple[int, ...]
    """
    Args:
        arg1: blah

    Returns:
        blah
    """
    return tuple(
        int(arg) for arg in arg1
    )
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


def test_py2_syntax():
    content = '''
class OtherClass(object):
    raise ValueError, "WTF python 2"


def one(arg2):
    """
    Args:
        arg2 (str): blah

    Returns:
        my.module.SomeClass[str]: blah
    """
    try:
        SomeClass([])
    except TypeError, e:
        # disgusting Python 2.5 except format
        pass
    return SomeClass(arg2)


def two(arg1):
    """
    Args:
        arg1 (Tuple[str, ...]): blah

    Returns:
        Tuple[my.module.SomeClass[str], ...]: blah
    """
    print "Python 2 print statement"
    print("parenthesised print statement")
    return tuple(
        one(arg) for arg in arg1
    )
'''

    expected = '''from my.module import SomeClass
from typing import Tuple


class OtherClass(object):
    raise ValueError, "WTF python 2"


def one(arg2):
    # type: (str) -> SomeClass[str]
    """
    Args:
        arg2: blah

    Returns:
        blah
    """
    try:
        SomeClass([])
    except TypeError, e:
        # disgusting Python 2.5 except format
        pass
    return SomeClass(arg2)


def two(arg1):
    # type: (Tuple[str, ...]) -> Tuple[SomeClass[str], ...]
    """
    Args:
        arg1: blah

    Returns:
        blah
    """
    print "Python 2 print statement"
    print("parenthesised print statement")
    return tuple(
        one(arg) for arg in arg1
    )
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION="2",
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


def test_py3_syntax():
    content = '''
class OtherClass(object):
    raise ValueError("WTF python 2")


def one(arg2):
    """
    Args:
        arg2 (str): blah

    Returns:
        my.module.SomeClass[str]: blah
    """
    try:
        SomeClass([])
    except TypeError as e:
        pass
    return SomeClass(arg2)


def two(arg1):
    """
    Args:
        arg1 (Tuple[str, ...]): blah

    Returns:
        Tuple[my.module.SomeClass[str], ...]: blah
    """
    print("print function with kwarg", end='end')
    return tuple(
        one(arg) for arg in arg1
    )
'''

    expected = '''from my.module import SomeClass
from typing import Tuple


class OtherClass(object):
    raise ValueError("WTF python 2")


def one(arg2):
    # type: (str) -> SomeClass[str]
    """
    Args:
        arg2: blah

    Returns:
        blah
    """
    try:
        SomeClass([])
    except TypeError as e:
        pass
    return SomeClass(arg2)


def two(arg1):
    # type: (Tuple[str, ...]) -> Tuple[SomeClass[str], ...]
    """
    Args:
        arg1: blah

    Returns:
        blah
    """
    print("print function with kwarg", end='end')
    return tuple(
        one(arg) for arg in arg1
    )
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION="3.6",
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected


def test_py2_with_print_function_syntax():
    content = '''
from __future__ import print_function


class OtherClass(object):
    raise ValueError, "WTF python 2"


def one(arg2):
    """
    Args:
        arg2 (str): blah

    Returns:
        my.module.SomeClass[str]: blah
    """
    try:
        SomeClass([])
    except TypeError, e:
        # disgusting Python 2.5 except format
        pass
    return SomeClass(arg2)


def two(arg1):
    """
    Args:
        arg1 (Tuple[str, ...]): blah

    Returns:
        Tuple[my.module.SomeClass[str], ...]: blah
    """
    print("parenthesised print statement", end='end')
    return tuple(
        one(arg) for arg in arg1
    )
'''

    expected = '''
from __future__ import print_function
from my.module import SomeClass
from typing import Tuple


class OtherClass(object):
    raise ValueError, "WTF python 2"


def one(arg2):
    # type: (str) -> SomeClass[str]
    """
    Args:
        arg2: blah

    Returns:
        blah
    """
    try:
        SomeClass([])
    except TypeError, e:
        # disgusting Python 2.5 except format
        pass
    return SomeClass(arg2)


def two(arg1):
    # type: (Tuple[str, ...]) -> Tuple[SomeClass[str], ...]
    """
    Args:
        arg1: blah

    Returns:
        blah
    """
    print("parenthesised print statement", end='end')
    return tuple(
        one(arg) for arg in arg1
    )
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION="2.7",
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=ImportCollisionPolicy.IMPORT,
            UNPATHED_TYPE_POLICY=UnpathedTypePolicy.FAIL,
        )
        inject.clear_and_configure(configuration_factory(test_settings))

        annotate(
            f.name, in_process=True, interactive=False, write=True, silent=True,
        )

        with open(f.name, "r") as fr:
            annotated = fr.read()

    assert annotated == expected
