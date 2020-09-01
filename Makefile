.PHONY: pypi, tag, shell, typecheck, pytest, pytest-pdb, test

pypi:
	rm -rf dist/*
	poetry publish --build
	make tag

tag:
	git tag $$(python -c "from waterloo.__about__ import __version__; print(__version__)")
	git push --tags

shell:
	PYTHONPATH=waterloo:tests:$$PYTHONPATH ipython

typecheck:
	# `-d import-error` needed due to issue with pydantic
	pytype -d import-error waterloo

pytest:
	py.test -v -s tests/

pytest-pdb:
	py.test -v -s --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb tests/

test:
	$(MAKE) typecheck
	$(MAKE) pytest
