#!/usr/bin/env bash
# Development mode: runs the FastAPI backend (with reload) and the Vite dev
# server side by side. Frontend on :5173 proxies /api to the backend on :8000.
#
# The dev server is a different origin, so TIMBRE_DEV tells the backend to
# accept it.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
source "$ROOT/preflight.sh"
timbre_preflight yes || exit 1

if [ ! -d "backend/.venv" ]; then
  python3 -m venv backend/.venv
fi
# shellcheck disable=SC1091
source backend/.venv/bin/activate
pip install -q -r backend/requirements-dev.txt

export TIMBRE_DEV=1

( cd backend && uvicorn app.main:app --reload --port 8000 ) &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT

( cd frontend && npm install && npm run dev )
