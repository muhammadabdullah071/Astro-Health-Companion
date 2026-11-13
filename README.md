# Astro-Health Companion: Elthiero's backend package

Everything for the backend and integration owner role: FastAPI, SQLite, seed script,
baseline and rules engine, assistant wiring with safe fallback, real status checks,
one command start, reset script, Docker, tests and checklists.

All demo data is **SIMULATED**. Decision support only, not a medical diagnosis.

## Quick start

macOS / Linux:
```
./scripts/run_local.sh
```
Windows:
```
scripts\run_local.bat
```
Then open http://127.0.0.1:8000/docs . The database is created and seeded on first start.

Check everything works (server running in another terminal):
```
python scripts/smoke_test.py
```
Run the tests (49 tests): `./scripts/run_tests.sh`

Docker (optional): `docker compose up --build`  (see docs/running-with-docker.md)

Rebuild the demo database at any time: `./scripts/reset_demo.sh` or `scripts\reset_demo.bat`

## Settings (optional .env)

No configuration is required. To change a setting, copy `.env.example` to `.env` in the repo
root and uncomment the lines you need. Priority: real environment variables, then `.env`,
then the built-in defaults in `backend/app/config.py`. Never commit `.env`.

## Ignore and Docker files (one set per folder)

| Folder | Git ignore | Docker files |
|--------|------------|--------------|
| repo root | `.gitignore` (secrets, `data/runtime`, `rag/index`, large files, OS and editor junk) | `docker-compose.yml` |
| `backend/` | `.gitignore` (Python caches, `.venv`, test caches, local databases) | `Dockerfile`, `.dockerignore` |
| `frontend/` | `.gitignore` (`node_modules`, `.next`, `.env*.local`) | `Dockerfile`, `.dockerignore` |

The backend image holds only backend code. Compose mounts `contract/`, `data/sample/`,
`data/runtime/` and `rag/` into it. See docs/running-with-docker.md.

## Folder map

```
backend/app/
  main.py                FastAPI app, CORS, auto-seed on first start
  config.py              all settings (environment variables, with defaults)
  errors.py              one error shape for every error
  db/schema.sql          tables: profile, readings, alerts
  db/seed.py             rebuilds the database (idempotent)
  engine/rules_config.py ALL thresholds (placeholders until Ammara confirms)
  engine/baseline.py     7-day personal baseline, streak helper, trend slope
  engine/rules.py        one function per rule, evaluate() sorts and numbers alerts
  engine/service.py      database to rules glue, stores alerts
  services/rag_adapter.py calls Cesar's rag/ask.py with timeout and fallback
  services/rag_stub.py    placeholder assistant used until Cesar's module exists
  services/health.py     real checks for /api/status
  routes/                status, profile, readings, alerts, assistant
backend/tests/           49 tests (rules, baseline, contract, endpoints, assistant, status, seed)
contract/examples/       one JSON file per endpoint (the frozen v1 contract)
data/generate_placeholder_data.py   placeholder SIMULATED data with planted anomalies
data/sample/readings.csv            30 days, ends 2026-11-14, ready to seed
scripts/                 run_local, reset_demo, run_tests, run_docker, smoke_test
docs/                    CHECKLISTS.md, PLACEHOLDERS.md, api-contract.md, running-with-docker.md
```

## Endpoints (contract v1)

| Method | Path | Purpose |
|--------|------|---------|
| GET | /api/status | backend, offline flag, LLM state, documents indexed, last data update |
| GET | /api/profile | demo astronaut and mission day |
| GET | /api/readings?days=14 | readings, oldest first, always with data_label |
| GET | /api/alerts | active alerts, most severe first |
| POST | /api/assistant/ask | question (and optional alert_id) in, answer and citations out |

Every error looks like `{"error": {"code": "NOT_FOUND", "message": "..."}}`.

## How the pieces connect

1. `seed.py` loads readings and runs the rules on the latest reading, storing alerts.
2. The API only reads the database, so responses are fast and identical every time.
3. `/api/assistant/ask` looks up the alert, then calls Cesar's `ask()` with a timeout
   (default 20 s). On timeout, crash or bad output it returns retrieval-only mode, never a 500.
4. If `rag/ask.py` does not exist yet, a clearly marked placeholder answer is returned.

## What you must replace later

See docs/PLACEHOLDERS.md for the full list. In short: thresholds (Ammara), sample data
(Sofia), `rag/ask.py` and `rag/index/meta.json` (Cesar), citations (Ammara and Cesar).
