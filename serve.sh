#!/bin/bash
# serve.sh — Development server with live rebuild on .src.md / .bib changes
#
# Flow:
#   1. build.sh runs once to ensure content/ is up to date
#   2. watchexec watches *.src.md and *.bib in the background and re-runs build.sh
#   3. zola serve runs in the foreground; picks up updated *.md and hot-reloads
#
# Requirements:
#   - pandoc  ≥ 2.11  (https://pandoc.org/)
#   - watchexec        (brew install watchexec  /  cargo install watchexec-cli)
#   - zola    ≥ 0.20.0 (https://www.getzola.org/)

set -xto pipefail

echo "Initial build..."
bash build.sh

echo "Starting watcher..."
watchexec -e src.md,bib -- bash build.sh &
WATCHER_PID=$!

# Ensure the watcher is killed when this script exits (Ctrl-C or error)
trap 'kill "$WATCHER_PID" 2>/dev/null || true' EXIT

echo "Starting Zola..."
zola serve
