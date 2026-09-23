#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# SCRIPT: watch.sh
# DESCRIPTION: Monitors content and preprocessing dependencies for changes.
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
#   --watch:  Watch content, scripts, config, and available CSL directories
#   --filter: Glob patterns for files that trigger a rebuild.
#             Source, bibliography, style, and pipeline changes fire the build.
#             Generated *.md output files
#             never match these patterns, preventing an infinite rebuild loop.
#             NOTE: --exts cannot be used here because watchexec treats only the
#             last segment after the final dot as the "extension", so a file like
#             post.src.md has extension "md", not "src.md". Using --filter with
#             a glob pattern is the correct approach.
#   --clear:  Clear the screen on each rebuild (keeps things tidy)
#   --shell:  Run the command inside a bash shell

watch_args=(--watch "$WATCH_DIR" --watch "$SCRIPT_DIR")
for dependency_file in config.toml themes/persona/theme.toml themes/persona/config.toml; do
    if [[ -f "$dependency_file" ]]; then
        watch_args+=(--watch "$dependency_file")
    fi
done
for dependency_dir in citation-style themes/persona/citation-style; do
    if [[ -d "$dependency_dir" ]]; then
        watch_args+=(--watch "$dependency_dir")
    fi
done

watchexec \
    "${watch_args[@]}" \
    --filter "**/*.src.md" \
    --filter "**/*.bib" \
    --filter "**/*.csl" \
    --filter "**/*.sh" \
    --filter "**/*.toml" \
    --clear \
    --shell bash \
    "$BUILD_SCRIPT"
