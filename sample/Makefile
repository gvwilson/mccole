# Runnable tasks.

all: commands

HTML_IGNORES = 'Attribute "x-' 'Attribute "@click' 'Attribute "file"'

## build: build HTML
build:
	mccole build --links extras/links.txt

## lint: check code and project
lint:
	@mccole lint --html --links extras/links.txt

## serve: serve generated HTML
serve:
	@python -m http.server -d docs $(PORT)
