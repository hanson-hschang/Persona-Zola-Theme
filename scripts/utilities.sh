#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# SCRIPT: utilities.sh
# DESCRIPTION: A shared library of helper functions for the Zola/Pandoc pipeline.
#
# FUNCTIONS:
#   1. parse_config_from_extra: Extracts a value from [extra] or [extra.theme].
#   2. find_csl_path:           Searches for a .csl file in provided directories.
#   3. split_source:            Separates frontmatter and body from .src.md.
# -----------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# parse_config_from_extra <content> <key> [theme_name] [default_value]
#   Extracts a value for <key> from [extra] or [extra.theme].
#   - Returns default_value if the key is missing.
#   - Fails with an error if key is missing AND no default is provided.
# ---------------------------------------------------------------------------
parse_config_from_extra() {
    local content="$1"
    local key="$2"
    local theme="${3:-}"
    local default_value="${4:-}"
    
    # 1. Validation
    if [[ -z "$content" ]]; then
        echo "  [ERROR] No content provided for configuration parsing." >&2
        return 1
    fi
    if [[ -z "$key" ]]; then
        echo "  [ERROR] No key provided for configuration parsing." >&2
        return 1
    fi
    
    local table="extra${theme:+.$theme}"
    
    # 2. Attempt to extract the value
    local result
    result=$(echo "$content" | awk -v table="$table" -v key="$key" '
        $0 == "[" table "]" {found=1; next} 
        found && /^\[/ {exit} 
        found && $0 ~ "^[ ]*" key {
            sub(/.*=[ ]*"/, ""); sub(/".*/, ""); print; exit
        }
    ')

    # 3. Handle Missing Keys
    if [[ -z "$result" ]]; then
        # If a default value is provided, return it; otherwise, return an error
        if [[ $# -ge 4 ]]; then
            echo "  [WARN] Key '$key' not found in [$table]. Using default value: $default_value" >&2
            echo "$default_value"
            return 0
        else
            echo "  [ERROR] Key '$key' not found in [$table] and no default provided." >&2
            return 1
        fi
    fi

    echo "$result"
}

# ---------------------------------------------------------------------------
# find_csl_path <style_name> <search_dirs_string>
#   Iterates through a space-separated string of directories to find <style_name>.csl
# ---------------------------------------------------------------------------
find_csl_path() {
    local style_name="$1"
    local search_dirs="$2"
    if [[ -z "$style_name" ]]; then
        echo "  [ERROR] No style name provided for CSL lookup." >&2
        return 1
    fi
    if [[ -z "$search_dirs" ]]; then
        echo "  [WARN] No search directories provided for CSL lookup." >&2
        return 1
    fi
    
    for d in $search_dirs; do
        if [[ -f "$d/${style_name}.csl" ]]; then
            echo "$d/${style_name}.csl"
            return 0
        fi
    done
    echo "  [WARN] Style '$style_name' not found in search paths. Checked paths:" >&2
    for d in $search_dirs; do
        echo "    - $d/" >&2
    done
    return 1
}

# ---------------------------------------------------------------------------
# split_source <file_path> <body_tmp_path>
#   Separates +++ frontmatter and body.
#   Returns: 0 on success (frontmatter to stdout), 1 on error (message to stderr).
# ---------------------------------------------------------------------------
split_source() {
    local file="$1"
    local body_tmp="$2"

    if [[ ! -f "$file" ]]; then
        echo "  [ERROR] Input file '$file' does not exist." >&2
        return 1
    fi

    if [[ -z "$body_tmp" ]]; then
        echo "  [ERROR] Internal Error: No temporary file path provided for body output." >&2
        return 1
    fi

    # Run awk and capture its exit status
    if ! awk -v body_file="$body_tmp" '
        /^\+\+\+/ { c++; next }
        c == 1 { print }
        c >= 2 { print > body_file }
        END { if (c < 2) exit 1 }
    ' "$file"; then
        echo "  [ERROR] $file: Missing valid +++ delimiters (Frontmatter error)." >&2
        return 1
    fi
}