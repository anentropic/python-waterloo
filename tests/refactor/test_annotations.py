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


def test_handle_splat_args():
    content = '''
def no_op(arg1, *args, **kwargs):
    """
    Args:
        arg1 (str): blah
        *args (int)
        **kwargs (Tuple[bool, ...])
    """
    return
'''

    expected = '''from typing import Tuple


def no_op(arg1, *args, **kwargs):
    # type: (str, *int, **Tuple[bool, ...]) -> None
    """
    Args:
        arg1: blah
        *args
        **kwargs
    """
    return
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
        ("arg1, arg2 = 'default'", {"arg1": ("int", "blah"), "arg2": ("str", "blah")},),
        (
            "arg1, arg2 = 'def,ault'",
            {"arg1": ("int", "blah"), "arg2": ("str", "blah")},
        ),
        (
            "arg1, arg2 = 3 * 7, *args, **kwargs",
            {
                "arg1": ("str", "blah"),
                "arg2": ("int", "blah"),
                "*args": ("bool", "blah"),
                "**kwargs": ("float", "blah"),
            },
        ),
        (
            "arg1, arg2 = (True, False), *args, **kwargs",
            {
                "arg1": ("str", "blah"),
                "arg2": (
                    "int",
                    "blah",
                ),  # wrong type if it was real code, but avoids having optional imports in the test
                "*args": ("bool", "blah"),
                "**kwargs": ("float", "blah"),
            },
        ),
        (
            "arg1, *, arg2 = 'default', **kwargs",
            {
                "arg1": ("int", "blah"),
                "arg2": ("str", "blah"),
                "**kwargs": ("float", "blah"),
            },
        ),
    ],
    ids=[
        "arg with default value",
        "arg with default value containing comma",
        "arg with statement as default value, *args and **kwargs",
        "arg with statement containing comma as default value, *args and **kwargs",
        "signature with keyword-only args and **kwargs",
    ],
)
def test_arg_annotation_signature_validate(signature, arg_annotations):
    annotations = "\n".join(
        f"        {name} ({type_}): {description}"
        for name, (type_, description) in arg_annotations.items()
    )
    content = f'''
def no_op({signature}):
    """
    Args:
{annotations}
    """
    pass
'''

    def splatify(name, type_):
        if name.startswith("**"):
            return f"**{type_}"
        elif name.startswith("*"):
            return f"*{type_}"
        else:
            return type_

    # I guess this is an 'oracle' i.e. an alternate implementation (meh)
    stripped_annotations = "\n".join(
        f"        {name}: {description}"
        for name, (_, description) in arg_annotations.items()
    )
    str_types = ", ".join(
        splatify(name, type_) for name, (type_, _) in arg_annotations.items()
    )
    type_comment = f"# type: ({str_types}) -> None"

    # only builtin types in examples, no imports needed
    expected = f'''
def no_op({signature}):
    {type_comment}
    """
    Args:
{stripped_annotations}
    """
    pass
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION="3.8",  # keyword-only args
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
def no_op({signature}):
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
    """
    NOTE: here is an example of a function where omitting the "Returns"
    block from the docstring and setting `REQUIRE_RETURN_TYPE=False` will
    give the wrong result (...an argument for `REQUIRE_RETURN_TYPE=True`)
    TODO: I don't know if there is any check for return statements we can
    do via Bowler?
    """
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


@pytest.mark.parametrize("python_version", [2, 3])
def test_returns_none(python_version):
    content = '''
def no_op(arg1):
    """
    Args:
        arg1 (Tuple[str, ...]): blah

    Returns:
        None
    """
    pass
'''

    # "Returns" block omitted since there was no description
    expected = '''from typing import Tuple


def no_op(arg1):
    # type: (Tuple[str, ...]) -> None
    """
    Args:
        arg1: blah
    """
    pass
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION=python_version,
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=True,
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
    "import_line,arg_type",
    [
        ("from a.package import a_module", "a_module.SomeClass"),
        ("import a.package.a_module", "a.package.a_module.SomeClass"),
    ],
)
@pytest.mark.parametrize("python_version", [2, 3])
def test_package_imports(python_version, import_line, arg_type):
    content = f'''{import_line}

def no_op(arg1):
    """
    Args:
        arg1 ({arg_type}): blah
    """
    pass
'''

    expected = f'''{import_line}

def no_op(arg1):
    # type: ({arg_type}) -> None
    """
    Args:
        arg1: blah
    """
    pass
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION=python_version,
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


@pytest.mark.parametrize(
    "import_collision_policy,expected_import,comment,remove_type",
    [
        (
            ImportCollisionPolicy.IMPORT,
            "from rest_framework.serializers import Serializer\n",
            "# type: (Serializer) -> None",
            True,
        ),
        (ImportCollisionPolicy.NO_IMPORT, "", "# type: (Serializer) -> None", True,),
        (ImportCollisionPolicy.FAIL, "", "", False,),
    ],
)
@pytest.mark.parametrize("python_version", [2, 3])
def test_dotted_path_annotation_star_import(
    python_version, import_collision_policy, expected_import, comment, remove_type
):
    content = '''from rest_framework.serializers import *

def no_op(arg1):
    """
    Args:
        arg1 (rest_framework.serializers.Serializer): blah
    """
    pass
'''

    if comment:
        comment = f"{comment}\n    "

    docstring_type = "" if remove_type else " (rest_framework.serializers.Serializer)"

    expected = f'''from rest_framework.serializers import *
{expected_import}
def no_op(arg1):
    {comment}"""
    Args:
        arg1{docstring_type}: blah
    """
    pass
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION=python_version,
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=import_collision_policy,
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
    "import_collision_policy,expected_import,comment,remove_type",
    [
        (
            ImportCollisionPolicy.IMPORT,
            "from serializers import Serializer\n\n",
            "# type: (Serializer) -> None",
            True,
        ),
        (ImportCollisionPolicy.NO_IMPORT, "", "# type: (Serializer) -> None", True,),
        (ImportCollisionPolicy.FAIL, "", "", False,),
    ],
)
@pytest.mark.parametrize("python_version", [2, 3])
def test_dotted_path_annotation_local_type_def(
    python_version, import_collision_policy, expected_import, comment, remove_type
):
    content = '''
class serializers:
    # why would you do this
    pass

def no_op(arg1):
    """
    Args:
        arg1 (serializers.Serializer): blah
    """
    pass
'''

    if comment:
        comment = f"{comment}\n    "

    docstring_type = "" if remove_type else " (serializers.Serializer)"

    expected = f'''{expected_import}
class serializers:
    # why would you do this
    pass

def no_op(arg1):
    {comment}"""
    Args:
        arg1{docstring_type}: blah
    """
    pass
'''

    with tempfile.NamedTemporaryFile(suffix=".py") as f:
        with open(f.name, "w") as fw:
            fw.write(content)

        test_settings = override_settings(
            PYTHON_VERSION=python_version,
            ALLOW_UNTYPED_ARGS=False,
            REQUIRE_RETURN_TYPE=False,
            IMPORT_COLLISION_POLICY=import_collision_policy,
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


def test_yields_generator():
    content = '''
def generator(arg1):
    """
    Args:
        arg1 (Iterable[int]): blah

    Yields:
        int: blah
    """
    for val in arg1:
        yield val
'''

    expected = '''from typing import Generator, Iterable


def generator(arg1):
    # type: (Iterable[int]) -> Generator[int, None, None]
    """
    Args:
        arg1: blah

    Yields:
        blah
    """
    for val in arg1:
        yield val
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


def test_method():
    """
    First arg is not annotatable
    """
    content = '''
class SomeClass:
    def method(obj, whatever):
        """
        Args:
            whatever (Any)
        """
        pass
'''

    expected = '''from typing import Any


class SomeClass:
    def method(obj, whatever):
        # type: (Any) -> None
        """
        Args:
            whatever
        """
        pass
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


def test_classmethod():
    """
    First arg is not annotatable
    """
    content = '''
class SomeClass:
    @classmethod
    def method(obj, whatever):
        """
        Args:
            whatever (Any)
        """
        pass
'''

    expected = '''from typing import Any


class SomeClass:
    @classmethod
    def method(obj, whatever):
        # type: (Any) -> None
        """
        Args:
            whatever
        """
        pass
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


def test_staticmethod():
    """
    First arg *is* annotatable
    """
    content = '''
class SomeClass:
    @staticmethod
    def method(obj, whatever):
        """
        Args:
            obj (object)
            whatever (Any)
        """
        pass
'''

    expected = '''from typing import Any


class SomeClass:
    @staticmethod
    def method(obj, whatever):
        # type: (object, Any) -> None
        """
        Args:
            obj
            whatever
        """
        pass
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
