# Runnable tasks.

PYTHON = uv run python

all: commands

## commands: show available commands (*)
commands:
	@grep -h -E '^##' ${MAKEFILE_LIST} \
	| sed -e 's/## //g' \
	| column -t -s ':'

## build: build package
build:
	${PYTHON} -m build

## docs: rebuild documentation
.PHONY: docs
docs:
	mkdocs build

## lint: check code and project
lint:
	@ruff check mccole tests

## test: run tests with coverage
test:
	${PYTHON} -m coverage run -m pytest tests && ${PYTHON} -m coverage report --show-missing

## clean: clean up
clean:
	@find . -type f -name '*~' -exec rm {} \;
	@find . -type d -name __pycache__ | xargs rm -r
	@find . -type d -name .pytest_cache | xargs rm -r
	@find . -type d -name .ruff_cache | xargs rm -r
