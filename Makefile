# Shared entry point for the theme demo and consuming sites.
SHELL := /usr/bin/env bash
PERSONA_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
ZOLA_ARGS ?=

.PHONY: help build serve check clean

help:
	@echo "make build  - Process Markdown and build public/"
	@echo "make serve  - Watch Markdown, citations, math, and site assets"
	@echo "make check  - Process Markdown and check the site"
	@echo "make clean  - Remove generated output; preserve authored content"

build:
	python3 -B "$(PERSONA_DIR)scripts/persona.py" build --root "$(CURDIR)" -- $(ZOLA_ARGS)

serve:
	python3 -B "$(PERSONA_DIR)scripts/persona.py" serve --root "$(CURDIR)" -- $(ZOLA_ARGS)

check:
	python3 -B "$(PERSONA_DIR)scripts/persona.py" check --root "$(CURDIR)" -- $(ZOLA_ARGS)

clean:
	python3 -B "$(PERSONA_DIR)scripts/persona.py" clean --root "$(CURDIR)"
