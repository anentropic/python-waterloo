# Haskell:

`IndentationSensitiveParsing.hs`

Comes from:
https://markkarpov.com/megaparsec/indentation-sensitive-parsing.html

```bash
cd waterloo-haskell
stack test
```

See `waterloo-haskell/package.yaml`

See also:
http://akashagrawal.me/beginners-guide-to-megaparsec/


# Python
```bash
pipenv shell
make test
```

This will (ultimately) parse python files with type-annotated docstrings specified in 'Napoleon'
format and re-apply the extracted annotations as mypy py2-compatible 'type comments'.

If your code is for Python 3 you can then run this tool https://github.com/ilevkivskyi/com2ann
and it will convert the py2 type-comments into py3 PEP-484 type annotations.
