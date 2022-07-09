SRC=mccole

# Show help by default.
.DEFAULT_GOAL := help

## help: show available commands
.PHONY: help
help:
	@grep -h -E '^##' ${MAKEFILE_LIST} | sed -e 's/## //g' | column -t -s ':'

## build: build and check package
.PHONY: build
build:
	python setup.py sdist bdist_wheel
	twine check dist/*

## upload: push package to PyPi Test
upload:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

## install: build package and install locally
.PHONY: install
install:
	pip install -e .

## lint: run software quality checks
.PHONY: lint
lint:
	@-flake8
	@-isort --check .
	@-black --check .
	@-pydocstyle --convention=google --count ${SRC}

## reformat: reformat code in place
.PHONY: reformat
reformat:
	@isort .
	@black .

## clean: remove junk files
.PHONY: clean
clean:
	@find . -name '*~' -exec rm {} \;
	@find . -name __pycache__ -delete
	@find . -name .DS_Store -exec rm {} \;
	@rm -rf build dist htmlcov mccole.egg-info sample/_site
