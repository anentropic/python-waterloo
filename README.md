# Waterloo

![Waterloo](https://user-images.githubusercontent.com/147840/74556780-b1621b80-4f56-11ea-9b4a-6d34da996cd8.jpg)

[![Build Status](https://travis-ci.org/anentropic/python-waterloo.svg?branch=master)](https://travis-ci.org/anentropic/python-waterloo)
[![Latest PyPI version](https://badge.fury.io/py/waterloo.svg)](https://pypi.python.org/pypi/waterloo/)

![Python 3.7](https://img.shields.io/badge/Python%203.7--brightgreen.svg)
![Python 3.8](https://img.shields.io/badge/Python%203.8--brightgreen.svg)  
(...but for running on Python 2.7 code)

(Work In Progress: not yet released to PyPI)

A cli tool to convert type annotations found in 'Google-style' docstrings (as understood and documented by the [Sphinx Napoleon](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/) plugin) into PEP-484 type comments which can be checked statically using `mypy --py2`.

For an example of the format see https://github.com/anentropic/python-waterloo/blob/master/tests/fixtures/napoleon.py

After we parse the docstrings and prepare the type comments (and imports of mentioned types), the resulting modifications to the files is performed by [Bowler](https://pybowler.io/). This tool provides a few nice features such as an optional interactive "diff" interface (or just preview diffs without writing changes yet as a "dry run").

In short you can...
```
waterloo annotate my-project-dir/ --write
```
...and it will derive type comments from all of your typed docstrings and add them to the files.

To preview the changes without committing them:
```
waterloo annotate my-project-dir/ --show-diff
```

Waterloo itself requires Python 3.6 or later, but is designed for projects still on Python 2.7.


### Upgrading to Python 3

Adding type comments with `waterloo` can be an intermediate step. You can start type checking with `mypy` while you're still on Python 2.7.

Later when you're ready to upgrade you can then run this other tool https://github.com/ilevkivskyi/com2ann
and it will convert the py2 type-comments into proper py3 type annotations.
