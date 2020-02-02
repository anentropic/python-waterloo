.PHONY: pypi, tag, mypy, pytest, test, shell

pypi:
	rm -f dist/*
	python setup.py sdist
	twine upload --config-file=.pypirc dist/*
	make tag

tag:
	git tag $$(python -c "from waterloo.__about__ import __version__; print(__version__)")
	git push --tags

shell:
	PYTHONPATH=waterloo:tests:$$PYTHONPATH ipython

mypy:
	mypy --ignore-missing-imports --show-error-codes waterloo

pytest:
	py.test -v -s --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb tests/

test:
	$(MAKE) mypy
	$(MAKE) pytest
