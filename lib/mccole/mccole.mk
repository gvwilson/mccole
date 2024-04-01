# ----------------------------------------------------------------------
# Generic McCole Makefile
# ----------------------------------------------------------------------

# By default, show available commands (by finding '##' comments)
.DEFAULT: commands

# Absolute path to this file
# See https://stackoverflow.com/questions/18136918/how-to-get-current-relative-directory-of-your-makefile
MCCOLE := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

# Project root directory
ROOT := .

# All Markdown source pages
SRC_PAGES := $(wildcard ${ROOT}/src/*.md) $(wildcard ${ROOT}/src/*/index.md)

# Standard GitHub pages (in root directory rather than website source directory)
GITHUB_PAGES := ${ROOT}/CODE_OF_CONDUCT.md ${ROOT}/LICENSE.md

# Information files
INFO_GLOSSARY := ${ROOT}/info/glossary.yml

# Generated HTML pages
DOCS_PAGES := $(patsubst ${ROOT}/src/%.md,${ROOT}/docs/%.html,$(SRC_PAGES))

## commands: show available commands
.PHONY: commands
commands:
	@grep -h -E '^##' ${MAKEFILE_LIST} \
	| sed -e 's/## //g' \
	| column -t -s ':'

## build: rebuild site without running server
.PHONY: build
build:
	ark build
	@touch ${ROOT}/docs/.nojekyll

## serve: build site and run server
.PHONY: serve
serve:
	ark watch

## style: check Python code style
.PHONY: style
style:
	@ruff check .

## reformat: reformat unstylish Python code
.PHONY: reformat
reformat:
	@ruff format .

## clean: clean up stray files
.PHONY: clean
clean:
	@find ${ROOT} -name '*~' -exec rm {} \;
	@find ${ROOT} -name '*.bkp' -exec rm {} \;
	@find ${ROOT} -name '.*.dtmp' -exec rm {} \;
	@find ${ROOT} -type d -name __pycache__ | xargs rm -r
	@find ${ROOT} -type d -name .pytest_cache | xargs rm -r
