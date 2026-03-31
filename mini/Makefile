## commands: show available commands (*)
commands:
	@grep -h -E '^##' ${MAKEFILE_LIST} \
	| sed -e 's/## //g' \
	| column -t -s ':'

## plain: build HTML with default settings
plain:
	@rm -rf ./docs
	@mccole create --dst . --force
	@mccole build --src . --dst docs

## forma: build HTML with forma
forma:
	@rm -rf ./docs
	@mccole create --dst . --force
	@mccole build --forma --src . --dst docs

## clean: clean up
clean:
	@find . -type f -name '*~' -exec rm {} \;
	@find . -type d -name __pycache__ | xargs rm -r

## check: check code and project
check:
	@mccole check --src . --dst docs

## serve: serve generated HTML
serve:
	@python -m http.server -d docs $(PORT)
