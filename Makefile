# Runnable tasks.

all: commands

## commands: show available commands (*)
commands:
	@grep -h -E '^##' ${MAKEFILE_LIST} \
	| sed -e 's/## //g' \
	| column -t -s ':'

## docs: rebuild documentation
.PHONY: docs
docs:
	mkdocs build

## lint: check code and project
lint:
	@ruff check mccole

## site: create documentation
site:
	mkdocs build

## serve: serve documentation
serve:
	mkdocs serve

## clean: clean up
clean:
	@rm -rf dist docs mccole.egg-info
	@find . -type f -name '*~' -exec rm {} \;
	@find . -type d -name __pycache__ | xargs rm -r
	@find . -type d -name .pytest_cache | xargs rm -r
	@find . -type d -name .ruff_cache | xargs rm -r
