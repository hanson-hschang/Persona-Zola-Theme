#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# SCRIPT: process_post.sh
# DESCRIPTION: Processes a single .src.md file into a Zola-compatible .md file.
#              Fails immediately if required arguments are missing.
#
# USAGE:
# ./process_post.sh <input_file> <default_csl> [csl_directories]
# -----------------------------------------------------------------------------

# Exit immediately
#   (1) if any command fails (-e), 
#   (2) if any variable is unset (-u), or 
#   (3) if any command in a pipeline fails (-o pipefail)
set -euo pipefail

# ---------------------------------------------------------------------------
# Usage function to display help message
# ---------------------------------------------------------------------------
usage() {
    echo "Usage: $0 <input_file> <default_csl> [csl_directories]" >&2
    exit 0
}

# Allow a manual help check
[[ "$1" == "-h" || "$1" == "--help" ]] && usage

# ---------------------------------------------------------------------------
# Argument Parsing
# ---------------------------------------------------------------------------
INPUT_FILE="${1:?Error: <input_file> is required.}"
DEFAULT_CSL="${2:?Error: <default_csl> is required.}"
CSL_DIRS_STR="${3:-}" 

# Check if the input file exists before proceeding
if [[ ! -f "$INPUT_FILE" ]]; then
    echo "Error: File not found: $INPUT_FILE" >&2
    usage
fi

# Source utilities for helper functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/utilities.sh" ]]; then
    source "$SCRIPT_DIR/utilities.sh"
else
    echo "Error: utilities.sh not found in $SCRIPT_DIR" >&2
    exit 1
fi

# Set up arguments
DIR=$(dirname "$INPUT_FILE")
NAME=$(basename "$INPUT_FILE" .src.md)
OUT_FILE="$DIR/$NAME.md"
DEFAULT_BIB_NAME="references.bib"

# ---------------------------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------------------------
echo "Processing $INPUT_FILE ..."

# 0. Prepare temporary files for processing; ensure they are cleaned up on exit
BODY_TMP=$(mktemp)
RENDERED_TMP=$(mktemp)
trap 'rm -f "$BODY_TMP" "$RENDERED_TMP"' EXIT

# --- 1. Split Frontmatter and Body ---
# If the file doesn't have valid delimiters, skip processing and print errors.
# The split_source function returns frontmatter to stdout and writes the body 
# to the provided temp file path. The frontmatter in a stored for later use.
if ! frontmatter=$(split_source "$INPUT_FILE" "$BODY_TMP"); then
    exit 1
fi

# --- 2. Resolve CSL Path ---
# The citation style is determined by checking, in order of priority:
#   (1) A style specified in the post's frontmatter ([extra].citation_style)
#   (2) The default CSL provided as an argument to this script
post_style=$(parse_config_from_extra "$frontmatter" "citation_style")
final_csl=""
# Try to find the user-specified style first (if it exists)
if [[ -n "$post_style" ]]; then
    final_csl=$(find_csl_path "$post_style" "$CSL_DIRS_STR") || \
    echo "  [WARN] Falling back to default CSL: $DEFAULT_CSL" >&2
fi
# If no user-specified style or the specified style was not found, use default
final_csl="${final_csl:-$DEFAULT_CSL}"
echo "  [INFO] Using CSL: $final_csl"

# --- 3. Resolve Bibliography Path ---
# The bibliography is determined by checking, in order of priority:
#   (1) A bibliography specified in the post's frontmatter ([extra].bibliography)
#   (2) A default "references.bib" in the same directory as the post
post_bib_file=$(parse_config_from_extra "$frontmatter" "bibliography" "" "$DEFAULT_BIB_NAME")
final_bib=""
if [[ -f "$DIR/$post_bib_file" ]]; then
    final_bib="$DIR/$post_bib_file"
    echo "  [INFO] Using bibliography: $final_bib"
else
    echo "  [WARN] Bibliography $post_bib_file not found at $DIR/." >&2
    echo "  [WARN] No bibliography will be used for this post." >&2
fi

# --- 4. Pandoc Rendering ---
# If a bibliography is found, use --citeproc with the specified CSL and bibliography.
# link-citations=true:            wraps each inline citation in <a href="#ref-key">.
# reference-section-title=...:   titles the auto-appended bibliography section.
# If no bibliography is found, render without citation processing.
cite_args=()
if [[ -n "$final_bib" ]]; then
    cite_args=(
        --citeproc
        --bibliography="$final_bib"
        --csl="$final_csl"
        --metadata link-citations=true
        --metadata reference-section-title=Bibliography
    )
fi
pandoc_args=(--wrap=none -t html -f markdown "$BODY_TMP" -o "$RENDERED_TMP")
if ! pandoc "${cite_args[@]}" "${pandoc_args[@]}"; then
    echo "  [ERROR] Pandoc failed to process: $INPUT_FILE" >&2
    echo "  [ERROR] Please check the bibliography and CSL files for issues." >&2
    exit 1
fi

# Normalize auto-generated bibliography heading from <h1> to <h2> so it sits
# at the same level as other section headings in the post body.
# Only targets <h1 class="unnumbered"> (Pandoc's auto-generated heading);
# user-written <h1> tags without that class are left untouched.
sed -i '' 's|<h1 class="unnumbered"\([^>]*\)>\([^<]*\)</h1>|<h2 class="unnumbered"\1>\2</h2>|g' "$RENDERED_TMP"

# --- 5. Reassemble ---
# Combine the original frontmatter with the rendered body and write to the output file.
{
    echo "+++"
    echo "$frontmatter"
    echo "+++"
    echo ""
    cat "$RENDERED_TMP"
} > "$OUT_FILE"

echo "  [SUCCESS] $INPUT_FILE -> $OUT_FILE"