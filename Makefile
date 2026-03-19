# -----------------------------------------------------------------------------
# Makefile for Persona
# 
# DESCRIPTION:
#   This Makefile orchestrates the conversion of source files (.src.md) 
#   into Zola-compatible Markdown using Pandoc and Perl post-processing.
#   It supports incremental builds, automated file watching with 'watchexec',
#   and live previewing via 'zola serve'.
#
# USAGE:
#   make build  - Perform a one-time incremental build of all modified posts.
#   make serve  - Run the watcher and Zola dev server simultaneously.
#   make clean  - Remove generated .md files to force a full rebuild.
# -----------------------------------------------------------------------------

# --- Variables ---
SHELL := /usr/bin/env bash
WATCH_SCRIPT := scripts/watch.sh
BUILD_SCRIPT := scripts/build.sh

# --- Targets ---

.PHONY: help build serve clean

help:
	@echo "Persona - Commands:"
	@echo "  make build  - Incremental Pandoc build"
	@echo "  make serve  - Watcher + Zola Live Server"
	@echo "  make clean  - Clean up generated content"

build:
	@bash $(BUILD_SCRIPT)

serve:
	@echo "--- Starting Watcher and Zola Server ---"
	# Runs the watcher in the background and Zola in the foreground.
	# Note: Use 'pkill -f watch.sh' if the background process persists after Ctrl+C.
	@bash $(WATCH_SCRIPT) & zola serve

clean:
	@echo "--- Cleaning Generated Files ---"
	@find content/ -name "*.src.md" | while read src; do \
		out="$${src%.src.md}.md"; \
		if [ -f "$$out" ]; then \
			rm "$$out"; \
			echo "  [REMOVED] $$out"; \
		fi; \
	done
	@echo "--- Clean Complete ---"