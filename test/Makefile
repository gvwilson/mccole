all: commands

## build: build HTML
build:
	mccole build --config project.toml

## commands: show available commands (*)
commands:
	@grep -h -E '^##' ${MAKEFILE_LIST} \
	| sed -e 's/## //g' \
	| column -t -s ':'

## lint: check code and project
lint:
	@mccole lint --config project.toml
	@html5validator --root docs --blacklist templates --ignore ${HTML_IGNORES} \
	&& echo "HTML checks passed."
