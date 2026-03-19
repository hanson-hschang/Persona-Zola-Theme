#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# SCRIPT: watch.sh
# DESCRIPTION: Monitors the content/ folder for changes and triggers build.sh.
#              Uses 'watchexec' for high-performance recursive monitoring.
#
# USAGE: 
#   ./scripts/watch.sh
# -----------------------------------------------------------------------------

# set -euo pipefail

# --- 1. Setup Paths ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_SCRIPT="$SCRIPT_DIR/build.sh"
WATCH_DIR="content"

# --- 2. Dependency Check ---
if ! command -v watchexec >/dev/null 2>&1; then
    echo "  [ERROR] 'watchexec' not found. Please install it first." >&2
    echo "  (e.g., 'brew install watchexec' or 'cargo install watchexec-cli')" >&2
    exit 1
fi

# --- 3. Execution ---
echo "--- Watchexec Mode Started ---"
echo "  [MONITORING] $WATCH_DIR/"
echo "  [TRIGGER]    $BUILD_SCRIPT"

# watchexec flags:
#   --watch:  Watch the content directory
#   --filter: Glob patterns for files that trigger a rebuild.
#             "**/*.src.md" and "**/*.bib" are used so only source and
#             bibliography changes fire the build.  Generated *.md output files
#             never match these patterns, preventing an infinite rebuild loop.
#             NOTE: --exts cannot be used here because watchexec treats only the
#             last segment after the final dot as the "extension", so a file like
#             post.src.md has extension "md", not "src.md". Using --filter with
#             a glob pattern is the correct approach.
#   --clear:  Clear the screen on each rebuild (keeps things tidy)
#   --shell:  Run the command inside a bash shell
#   --postpone: Skips the initial run and waits for the first file event.

watchexec \
    --watch "$WATCH_DIR" \
    --filter "**/*.src.md" \
    --filter "**/*.bib" \
    --clear \
    --shell bash \
    --postpone \
    "$BUILD_SCRIPT"