# Runnable tasks.

all: commands

## lint: check code and project
lint:
	@ruff check mccole

## render: convert to HTML
render:
	mccole render \
	--css mccole/static/page.css \
	--exclude mccole.egg-info \
	--icon mccole/static/favicon.ico \
	--templates mccole/templates
	@touch docs/.nojekyll

## serve: serve generated HTML
serve:
	@python -m http.server -d docs $(PORT)

## clean: clean up
clean:
	@rm -rf dist docs mccole.egg-info
	@find . -type f -name '*~' -exec rm {} \;
	@find . -type d -name __pycache__ | xargs rm -r
	@find . -type d -name .pytest_cache | xargs rm -r
	@find . -type d -name .ruff_cache | xargs rm -r
