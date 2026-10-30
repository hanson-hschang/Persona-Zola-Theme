#!/usr/bin/env bash
# Run from a site root, or from the Persona repository to build its demo.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 -B "$SCRIPT_DIR/persona.py" build --root "$PWD" -- "$@"
