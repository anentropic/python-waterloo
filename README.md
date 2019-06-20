`IndentationSensitiveParsing.hs`

Comes from:
https://markkarpov.com/megaparsec/indentation-sensitive-parsing.html

Install dependencies:
```bash
stack install megaparsec-6.2.0
```

for code from the Megaparsec test suite you also need:
```bash
stack install QuickCheck-2.9.2
stack install hspec-megaparsec-1.1.0
```

Run:
```bash
stack runghc IndentationSensitiveParsing.hs {string to parse}

stack runghc IndentationSensitiveParsing.hs "$(< {file to parse})"
```

See also:
http://akashagrawal.me/beginners-guide-to-megaparsec/



Python
```bash
pyenv activate waterloo
pytest test_simple.py
```
