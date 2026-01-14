#!/usr/bin/env bash
# One-command local launcher for Timbre.
#
# Installs backend dependencies into a venv, rebuilds the frontend when dist is
# missing or any source file is newer than the last build, and serves the whole
# app from http://localhost:8000.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "$ROOT/preflight.sh"
timbre_preflight yes || exit 1

if [ ! -d "backend/.venv" ]; then
  echo "→ Creating Python virtual environment…"
  python3 -m venv backend/.venv
fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate
echo "→ Installing backend dependencies…"
pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

needs_build=0
if [ ! -f "frontend/dist/index.html" ]; then
  needs_build=1
elif [ -n "$(find frontend/src frontend/index.html frontend/package.json -newer frontend/dist/index.html 2>/dev/null)" ]; then
  needs_build=1
fi

if [ "$needs_build" -eq 1 ]; then
  echo "→ Building frontend…"
  ( cd frontend && npm install --silent && npm run build )
else
  echo "→ Frontend is up to date."
fi

echo "→ Timbre is starting on http://localhost:8000"
cd backend
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
