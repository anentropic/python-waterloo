# Waterloo

![Waterloo](https://user-images.githubusercontent.com/147840/74556780-b1621b80-4f56-11ea-9b4a-6d34da996cd8.jpg)

[![Build Status](https://travis-ci.org/anentropic/python-waterloo.svg?branch=master)](https://travis-ci.org/anentropic/python-waterloo)
[![Latest PyPI version](https://badge.fury.io/py/waterloo.svg)](https://pypi.python.org/pypi/waterloo/)

![Python 3.7](https://img.shields.io/badge/Python%203.7--brightgreen.svg)
![Python 3.8](https://img.shields.io/badge/Python%203.8--brightgreen.svg)  
(...but for running on Python 2.7 code)

A cli tool to convert type annotations found in 'Google-style' docstrings (as understood and documented by the [Sphinx Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/) plugin) into PEP-484 type comments which can be checked statically using `mypy --py2`.

For an example of the format see https://github.com/anentropic/python-waterloo/blob/master/tests/fixtures/napoleon.py

### Installation

Waterloo itself requires Python 3.6 or later, but is designed for projects still on Python 2.7.

For this reason it is best installed using [pipx](https://github.com/pipxproject/pipx):

```
$ pipx install waterloo
  installed package waterloo 0.1.1, Python 3.7.6
  These apps are now globally available
    - waterloo
done! ✨ 🌟 ✨
```

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
waterloo annotate [-h] [--indent INDENT]
                       [--max-indent-level MAX_INDENT_LEVEL] [-aa] [-rr] [-w]
                       [-s] [-i]
                       F [F ...]

positional arguments:
  F                    List of file or directory paths to process.
```

**options:**

| arg  | description |
| ------------- | ------------- |
| `-aa, --allow-untyped-args` | If any args or return types are found in docstring we can attempt to output a type annotation. If arg types are missing or incomplete, default behaviour is to raise an error. If this flag is set we will instead output an annotation like `(...) -> returnT` which mypy will treat as if all args are `Any`. (default: `False`) |
| `-rr, --require-return-type` | If any args or return types are found in docstring we can attempt to output a type annotation. If the return type is missing our default behaviour is to assume function should be annotated as returning `-> None`. If this flag is set we will instead raise an error. (default: `False`) |
| `-w, --write` | Whether to apply the changes to target files. Without this flag set waterloo will just perform a 'dry run'. (default: `False`) |
| `-s, --show-diff` | Whether to print the hunk diffs to be applied. (default: `False`) |
| `-i, --interactive` | Whether to prompt about applying each diff hunk. (default: `False`) |

**waterloo.toml**

You can also define a `waterloo.toml` file in the root of your project to provide your own defaults to some of these options:

```toml
python_version = 3
indent = 2
max_indent_level = 15

allow_untyped_args = false
require_return_type = true
```

**Environment vars**

You can also provide config defaults via environment variables, e.g.:
```bash
WATERLOO_PYTHON_VERSION=3
WATERLOO_INDENT=2
WATERLOO_MAX_INDENT_LEVEL=15

WATERLOO_ALLOW_UNTYPED_ARGS=false
WATERLOO_REQUIRE_RETURN_TYPE=true
```

### Upgrading your project to Python 3

Adding type comments with `waterloo` can be an intermediate step. You can start type checking with `mypy` while you're still on Python 2.7.

Later when you're ready to upgrade you can then run this other tool https://github.com/ilevkivskyi/com2ann
and it will convert the py2 type-comments into proper py3 type annotations.
