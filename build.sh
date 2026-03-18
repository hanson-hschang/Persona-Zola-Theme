#!/bin/bash
# build.sh — Pandoc citation preprocessing pipeline
#
# Converts every *.src.md file in content/ into a Zola-renderable *.md file
# by running Pandoc --citeproc on the post body.
#
# CSL priority order (highest to lowest):
#   1. per-post [extra].citation_style  →  styles/<value>.csl
#   2. local style.csl in the same directory as the .src.md
#   3. config.toml [extra].citation_style  →  styles/<value>.csl
#   4. theme.toml  [extra].citation_style  →  styles/<value>.csl
#   5. error: exit 1

set -euo pipefail

STYLES_DIR="styles"

# ---------------------------------------------------------------------------
# parse_style <file>
#   Reads [extra] block from a TOML file and extracts the citation_style value.
#   Stops at the next section header so it does not read [extra.persona] etc.
# ---------------------------------------------------------------------------
parse_style() {
  awk '/^\[extra\]/{found=1; next} found && /^\[/{exit} found{print}' "$1" \
    | grep '^[^#]*citation_style' | head -1 | sed 's/.*= *"\(.*\)"/\1/'
}

theme_style=""
config_style=""

[ -f theme.toml ]  && theme_style=$(parse_style theme.toml)
[ -f config.toml ] && config_style=$(parse_style config.toml)

# Resolve site-wide default: config > theme > error
if [ -n "$config_style" ] && [ -f "$STYLES_DIR/$config_style.csl" ]; then
  DEFAULT_CSL="$STYLES_DIR/$config_style.csl"
elif [ -n "$theme_style" ] && [ -f "$STYLES_DIR/$theme_style.csl" ]; then
  DEFAULT_CSL="$STYLES_DIR/$theme_style.csl"
else
  echo "Error: no valid citation_style found in theme.toml or config.toml" >&2
  echo "  Set [extra].citation_style to the name of a .csl file in $STYLES_DIR/" >&2
  exit 1
fi

echo "Default CSL: $DEFAULT_CSL"

find content/ -name "*.src.md" | while IFS= read -r f; do
  dir=$(dirname "$f")
  name=$(basename "$f" .src.md)
  bib="$dir/references.bib"
  out="$dir/$name.md"

  echo "Processing $f..."

  # Extract the content between the opening +++ and the closing +++
  frontmatter=$(awk '/^\+\+\+/{p++; next} p==1{print} p==2{exit}' "$f")

  # Per-post override: look for citation_style in the front matter [extra] block
  post_style=$(echo "$frontmatter" \
    | awk '/^\[extra\]/{found=1; next} found && /^\[/{exit} found{print}' \
    | grep '^[^#]*citation_style' | head -1 \
    | sed 's/.*= *"\(.*\)"/\1/')

  if [ -n "$post_style" ] && [ -f "$STYLES_DIR/$post_style.csl" ]; then
    csl="$STYLES_DIR/$post_style.csl"
  elif [ -f "$dir/style.csl" ]; then
    csl="$dir/style.csl"
  else
    csl="$DEFAULT_CSL"
  fi

  # Find the line number of the closing +++
  second=$(grep -n "^\+\+\+" "$f" | sed -n '2p' | cut -d: -f1)

  # Run Pandoc on the body only (everything after the closing +++)
  if [ -f "$bib" ]; then
    body=$(tail -n +"$((second + 1))" "$f" \
      | pandoc --citeproc --bibliography="$bib" --csl="$csl" \
               --wrap=none -t gfm -f markdown)
  else
    body=$(tail -n +"$((second + 1))" "$f" \
      | pandoc --wrap=none -t gfm -f markdown)
  fi

  # Reassemble: front matter block + processed body
  printf '+++\n%s\n+++\n%s\n' "$frontmatter" "$body" > "$out"
  echo "  [$csl] → $out"
done

echo "Done."
