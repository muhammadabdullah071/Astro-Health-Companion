#!/usr/bin/env bash
# One command start (macOS / Linux). Creates the venv, installs packages, starts the API.
# The database is created and seeded automatically on first start.
# Dev mode with auto reload:  ./scripts/run_local.sh --reload
set -e
cd "$(dirname "$0")/../backend"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 "$@"
