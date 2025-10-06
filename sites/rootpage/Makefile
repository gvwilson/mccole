# Runnable tasks.

all: commands

## build: build HTML
build:
	mccole build --src . --dst docs --root homepage.md

## check: check code and project
check:
	@mccole check --src . --dst docs

## serve: serve generated HTML
serve:
	@python -m http.server -d docs $(PORT)
