# Waterloo

![Waterloo](https://user-images.githubusercontent.com/147840/74556780-b1621b80-4f56-11ea-9b4a-6d34da996cd8.jpg)

[![Build Status](https://travis-ci.org/anentropic/python-waterloo.svg?branch=master)](https://travis-ci.org/anentropic/python-waterloo)
[![Latest PyPI version](https://badge.fury.io/py/waterloo.svg)](https://pypi.python.org/pypi/waterloo/)

![Python 3.7](https://img.shields.io/badge/Python%203.7--brightgreen.svg)
![Python 3.8](https://img.shields.io/badge/Python%203.8--brightgreen.svg)  
_(...but primarily for running on Python 2.7 code)_

A cli tool to convert type annotations found in 'Google-style' docstrings (as understood and documented by the [Sphinx Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/) plugin) into PEP-484 type comments which can be checked statically using `mypy --py2`.

For an example of the format see https://github.com/anentropic/python-waterloo/blob/master/tests/fixtures/napoleon.py

### Installation

Waterloo itself requires Python 3.7 or later, but is primarily designed for projects having Python 2.7 source files.  
_(It can be run on Python 3 source files too, but since we add type-comments you will want to run the [comm2ann](https://github.com/ilevkivskyi/com2ann) tool afterwards to migrate those to Py3 annotations)._

For this reason it is best installed using [pipx](https://github.com/pipxproject/pipx):

```
$ pipx install waterloo
  installed package waterloo 0.5.0, Python 3.7.6
  These apps are now globally available
    - waterloo
done! ✨ 🌟 ✨
```

(NOTE: we currently have to install from GitHub due to using a forked version Bowler, PyPI installation will be available once our changes are upstreamed)

### Basic Usage

After we parse the docstrings and prepare the type comments (and imports of mentioned types), the resulting modifications to the files are performed by [Bowler](https://pybowler.io/). This tool provides a few nice features such as an optional interactive "diff" interface (or just preview diffs without writing changes yet as a "dry run").

In short you can...
```
waterloo annotate my-project-dir/ --write
```
...and it will derive type comments from all of your typed docstrings and add them to the files.

To preview the changes without committing them:
```
waterloo annotate my-project-dir/ --show-diff
```

### CLI options

```
usage: waterloo annotate [-h] [-p PYTHON_VERSION] [-aa] [-rr]
                         [-ic {IMPORT,NO_IMPORT,FAIL}] [-up {IGNORE,WARN,FAIL}]
                         [-w] [-s] [-i]
                         F [F ...]

positional arguments:
  F                     List of file or directory paths to process.
```

**Annotation options:**

| arg  | description |
| ---- | ----------- |
| `-p --python-version` | We can refactor either Python 2 or Python 3 source files but the underlying bowler+fissix libraries need to know which grammar to use (to know if `print` is a statement or a function). In Py2 mode, `print` will be auto-detected based on whether a `from __future__ import print_function` is found. For Py3 files `print` can only be a function. We also use `parso` library which can benefit from knowing `<major>.<minor>` version of your sources. (default: `2.7`) |
| `-aa, --allow-untyped-args` | If any args or return types are found in docstring we can attempt to output a type annotation. If arg types are missing or incomplete, default behaviour is to raise an error. If this flag is set we will instead output an annotation like `(...) -> returnT` which mypy will treat as if all args are `Any`. (default: `False`) |
| `-rr, --require-return-type` | If any args or return types are found in docstring we can attempt to output a type annotation. If the return type is missing our default behaviour is to assume function should be annotated as returning `-> None`. If this flag is set we will instead raise an error. (default: `False`) |
| `-ic --import-collision-policy {IMPORT,NO_IMPORT,FAIL}` | There are some cases where it is ambiguous whether we need to add an import for your documented type. This can occur if you gave a dotted package path but there is already a matching `from package import *`, or a relative import of same type name. In both cases it is safest for us to add a new specific import for your type, but it may be redundant. The default option `IMPORT` will add imports. The `NO_IMPORT` option will annotate without adding imports, and will also show a warning message. FAIL will print an error and won't add any annotation. (default: `IMPORT`) |
| `-up --unpathed-type-policy {IGNORE,WARN,FAIL}` | There are some cases where we cannot determine an appropriate import to add - when your types do not have a dotted path and we can't find a matching type in builtins, typing package or locals. When policy is `IGNORE` we will annotate as documented, you will need to resolve any errors raised by mypy manually. `WARN`option will annotate as documented but also display a warning. `FAIL` will print an error and won't add any annotation. (default: `FAIL`) |

**Apply options:**

| arg  | description |
| ---- | ----------- |
| `-w, --write` | Whether to apply the changes to target files. Without this flag set waterloo will just perform a 'dry run'. (default: `False`) |
| `-s, --show-diff` | Whether to print the hunk diffs to be applied. (default: `False`) |
| `-i, --interactive` | Whether to prompt about applying each diff hunk. (default: `False`) |

**waterloo.toml**

You can also define a `waterloo.toml` file in the root of your project to provide your own defaults to some of these options:

```toml
python_version = 3

allow_untyped_args = false
require_return_type = true
unpathed_type_policy = "IGNORE"
import_collision_policy = "FAIL"
```

**Environment vars**

You can also provide config defaults via environment variables, e.g.:
```bash
WATERLOO_PYTHON_VERSION=3

WATERLOO_ALLOW_UNTYPED_ARGS=false
WATERLOO_REQUIRE_RETURN_TYPE=true
UNPATHED_TYPE_POLICY='IGNORE'
IMPORT_COLLISION_POLICY='FAIL'
```

### Notes on 'Napoleon' docstring format

The format is defined here https://sphinxcontrib-napoleon.readthedocs.io/en/latest/

For now we only support the "Google-style" option. Open an issue if you need the alternative "Numpy-style" format.

In addition to the [official list](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/#docstring-sections) of Section headings we also allow `Kwargs:` (since I'd used that one myself in many places).

If you run waterloo with `--show-diff` option you will notice that we automatically add imports for the annotated types:

```diff
--- tests/fixtures/napoleon.py
+++ tests/fixtures/napoleon.py
@@ -2,6 +2,8 @@
 Boring docstring for the module itself
 """
 import logging
+from engine.models import Product
+from typing import Any, Callable, Dict, Iterable, List, Optional, Union

 logger = logging.getLogger(__name__)
```

Built-in types and those from `typing` module are recognised. For other types we can still generate the import as long as you use dotted-path syntax in the docstring, for example:

```python
"""
    Args:
        products (Union[Iterable[Dict], Iterable[engine.models.Product]])
        getter (Callable[[str], Callable])
"""
```

In this docstring, waterloo is able to add the `from engine.models import Product` import.

If your docstrings don't have dotted paths you will see warnings like:
```
⚠️  Could not determine imports for these types: MysteryType
   (will assume types already imported or defined in file)
```

Waterloo will still add the annotation to the function, but when you try to run mypy on this file it will complain that `MysteryType` is not imported (if `MysteryType` is not already imported or defined in the file). You will then have to resolve that manually.

You may want to run a formatter such as [isort](https://github.com/timothycrosley/isort) on your code after applying annotations with waterloo, since it will just append the imports to the bottom of your existing import block.

### Upgrading your project to Python 3

Adding type comments with `waterloo` can be an intermediate step. You can start type checking with `mypy` while you're still on Python 2.7.

Later when you're ready to upgrade you can then run this other tool https://github.com/ilevkivskyi/com2ann
and it will convert the py2 type-comments into proper py3 type annotations.
