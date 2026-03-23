# Runnable tasks.

all: commands

## commands: show available commands
commands:
	@grep -h -E '^##' ${MAKEFILE_LIST} \
	| sed -e 's/## //g' \
	| column -t -s ':'

## build: build package
build:
	python -m build

## check: check code issues
check:
	ruff check .

## clean: clean up
clean:
	@rm -rf ./dist
	@find . -path './.venv' -prune -o -type d -name '__pycache__' -exec rm -rf {} +
	@find . -path './.venv' -prune -o -type f -name '*~' -exec rm {} +
	@find . -path './.venv' -prune -o -type d -name '.pytest_cache' -exec rm -rf {} +
	@find . -path './.venv' -prune -o -type d -name '.coverage' -exec rm {} +

## docs: build documentation
docs:
	@mkdocs build
	@touch docs/.nojekyll
	@cp docs-requirements.txt docs/requirements.txt

## fix: fix code issues
fix:
	@ruff check --fix .

## format: format code
format:
	@ruff format .

## publish: publish using ~/.pypirc credentials
publish:
	twine upload --verbose dist/*

## serve: serve documentation
serve:
	python -m http.server -d docs

## test: run tests
test:
	python -m pytest tests
