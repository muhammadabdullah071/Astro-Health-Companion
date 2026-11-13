#!/usr/bin/env bash
# Rebuild the database to the known demo state in seconds (macOS / Linux).
set -e
cd "$(dirname "$0")/../backend"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
python -m app.db.seed
