#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# SCRIPT: build.sh
# DESCRIPTION: Converts every *.src.md file in content/ into Zola-renderable 
#              *.md files. Identifies global settings and delegates work to 
#              process_post.sh.
#
# USAGE: 
#   ./scripts/build.sh
# -----------------------------------------------------------------------------

# --- 1. Configuration ---
THEME_REPO_ISSUE="https://github.com/hanson-hschang/Persona-Zola-Theme/issues"
THEME_NAME="persona"
THEME_DIRECTORY="themes/${THEME_NAME}"
# Priority list for configuration files
CONFIG_FILES=("config.toml" "${THEME_DIRECTORY}/config.toml")
# Space-separated directories for CSL lookups
CSL_SEARCH_DIRS="citation-style ${THEME_DIRECTORY}/citation-style"

# --- 2. Setup & Utilities ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKER="$SCRIPT_DIR/process_post.sh"

# Source the shared utility library
if [[ -f "$SCRIPT_DIR/utilities.sh" ]]; then
    source "$SCRIPT_DIR/utilities.sh"
else
    echo "  [ERROR] utilities.sh not found in $SCRIPT_DIR" >&2
    exit 1
fi

# Ensure the worker script is executable
chmod +x "$WORKER"

# --- 3. Resolve Global Default Style ---
config_content=""
default_csl_style=""
for config_file in "${CONFIG_FILES[@]}"; do
    if [[ -f "$config_file" ]]; then
        config_content=$(cat "$config_file")
        csl_style=$(parse_config_from_extra "$config_content" "citation_style" "$THEME_NAME")
        if [[ -n "$csl_style" ]]; then
            default_csl_style="$csl_style"
            echo "  [INFO] Found global citation style '$default_csl_style' in $config_file"
            break
        fi
    fi
done

if [[ -z "$default_csl_style" ]]; then
    echo "  [ERROR] No global citation style found in config files." >&2
    echo "     Please check if the theme is up to date or report this issue to the theme maintainer." >&2
    echo "     Issue tracker: $THEME_REPO_ISSUE" >&2
    exit 1
fi

# Find the full path for the default CSL file
default_csl_path=$(find_csl_path "$default_csl_style" "$CSL_SEARCH_DIRS")
if [[ -z "$default_csl_path" ]]; then
    echo "  [ERROR] Could not find CSL file for default style '$default_csl_style'." >&2
    exit 1
fi

# --- 4. Incremental Build Loop ---
echo "--- Starting Incremental Build ---"
echo "  [CONFIG] Global Style: $default_csl_style"
echo "  [CONFIG] Search Paths: $CSL_SEARCH_DIRS"

# Find all .src.md files and check modification times
find content/ -name "*.src.md" | while read -r src; do
    # Define the output path (e.g., post.src.md -> post.md)
    out="${src%.src.md}.md"

    # Incrementality Check:
    # Process only if the output file is missing OR the source is newer (-nt)
    if [[ ! -f "$out" || "$src" -nt "$out" ]]; then
        echo ""
        "$WORKER" "$src" "$default_csl_path" "$CSL_SEARCH_DIRS"
    fi
done

echo "--- Build Complete ---"