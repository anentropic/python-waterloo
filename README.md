# Waterloo

(Work In Progress: not yet released to PyPI)

A cli tool to convert type annotations found in 'Google-style' docstrings (as understood by e.g. [`sphinx.ext.napoleon`](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/)) into PEP-484 type comments which can be checked statically using `mypy --py2`.

For an example of the format see https://github.com/anentropic/python-waterloo/blob/master/tests/fixtures/napoleon.py

After we parse the docstrings and prepare the type comments (and imports of mentioned types), the resulting modifications to the files is performed by [Bowler](https://pybowler.io/). This tool provides a few nice features such as an optional interactive "diff" interface (or just preview diffs without writing changes yet as a "dry run").

In short you can...
```
waterloo my-project-dir/ --write --silent
```
...and it will derive type comments from all of your typed docstrings and add them to the files.

Waterloo itself requires Python 3.6 or later, but is designed for projects still on Python 2.7.


### Upgrading to Python 3

Adding type comments with `waterloo` can be an intermediate step. You can start type checking with `mypy` while you're still on Python 2.7.

Later when you're ready to upgrade you can then run this other tool https://github.com/ilevkivskyi/com2ann
and it will convert the py2 type-comments into proper py3 type annotations.
