#!/usr/bin/env bash
# Compatibility entry point: the shared server now owns watching and cleanup.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$SCRIPT_DIR/persona.py" serve --root "$PWD" -- "$@"
