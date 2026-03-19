# Makefile — Persona Zola Theme build helpers
#
# Targets:
#   serve  — run the citation preprocessor, start file watcher, then zola serve
#   build  — run the citation preprocessor then build the static site

.PHONY: serve build

serve:
	bash scripts/serve.sh

build:
	bash scripts/build.sh
	zola build
