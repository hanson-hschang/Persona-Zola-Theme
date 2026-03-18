# Makefile — Persona Zola Theme build helpers
#
# Targets:
#   dev    — run the citation preprocessor, start file watcher, then zola serve
#   build  — run the citation preprocessor then build the static site
#   clean  — remove all generated .md files (keeps .src.md files untouched)

.PHONY: dev build clean

dev:
	bash serve.sh

build:
	bash build.sh
	zola build

clean:
	find content/ -name "*.md" ! -name "*.src.md" -delete
