#!/usr/bin/env bash
# Batch-transcribe a whole folder into one document (macOS / Linux).
#
# Usage:
#   ./batch.sh --input /path/to/folder --languages ru,uk,en --model small --format md
#
# All arguments are passed straight through to `python -m app.batch`
# (run `./batch.sh --help` to see them).
#
# The process keeps running in the invoking directory, because every relative
# path the user typed is relative to that. Node is not needed: batch mode never
# touches the frontend.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CALLER_PWD="$PWD"

# shellcheck disable=SC1091
source "$ROOT/preflight.sh"
timbre_preflight no || exit 1

if [ ! -d "$ROOT/backend/.venv" ]; then
  python3 -m venv "$ROOT/backend/.venv"
fi
# shellcheck disable=SC1091
source "$ROOT/backend/.venv/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$ROOT/backend/requirements.txt"

cd "$CALLER_PWD"
PYTHONPATH="$ROOT/backend" exec python -m app.batch "$@"
