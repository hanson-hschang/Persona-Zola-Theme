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
#   -w: Watch the content directory
#   -r: Restart the command if it's already running (not strictly needed for build.sh)
#   -e: Extensions to filter (src.md and bib)
#   --ignore: Specifically ignore the generated .md files to prevent loops
#   --postpone: Wait for the first change before running (optional)
#   --shell: Run the command in a shell
#   --clear: Clear the screen on each rebuild (optional, keeps things tidy)

watchexec \
    --watch "$WATCH_DIR" \
    --exts src.md,bib \
    --ignore "**/*.md" \
    --clear \
    --shell bash \
    "$BUILD_SCRIPT"