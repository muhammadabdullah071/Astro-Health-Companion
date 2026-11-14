# Backend

FastAPI + SQLite service for the Astro-Health Companion. It stores simulated health readings, turns them into
transparent alerts with a rules engine, and connects the frontend to the offline assistant (`rag/`).
Everything runs locally and needs no internet.

> All data is **SIMULATED**. Decision support only, not a medical diagnosis.

**Owner:** Elthiero. Other pieces: the contract is in [`../docs/api-contract.md`](../docs/api-contract.md), the system
overview in [`../docs/architecture.md`](../docs/architecture.md), the assistant contract in
[`../rag/INTERFACE.md`](../rag/INTERFACE.md).

## Run it

Needs Python 3.10 or newer. From the repo root:

```bash
./scripts/run_local.sh          # macOS / Linux
scripts\run_local.bat           # Windows
```

This creates `backend/.venv`, installs `requirements.txt`, and starts the API on <http://127.0.0.1:8000>
(interactive docs at `/docs`). The database is created and seeded on first start.

Or by hand, from this folder:

```bash
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload                           # development, auto reload
python -m app.db.seed                                   # rebuild the database
python -m pytest                                        # tests
```

Other scripts (repo root): `./scripts/reset_demo.sh` rebuilds the database, `./scripts/run_tests.sh` runs the tests,
`python scripts/smoke_test.py` checks every endpoint of a running server.

## Endpoints

| Method | Path | Returns |
|--------|------|---------|
| GET | `/api/status` | backend, offline flag, model state, documents indexed, last data update |
| GET | `/api/profile` | the served astronaut and mission day |
| GET | `/api/readings?days=14` | readings, oldest first (`days` 1 to 90) |
| GET | `/api/alerts?days=14` | alerts from the last N days, most severe first |
| POST | `/api/assistant/ask` | answer, mode, citations and disclaimer |

Every error has one shape: `{"error": {"code": "NOT_FOUND", "message": "..."}}` (codes `NOT_FOUND`,
`VALIDATION_ERROR`, `METHOD_NOT_ALLOWED`, `INTERNAL_ERROR`). Timestamps are UTC with a trailing `Z`. Example
responses live in `../contract/examples/`, and a test fails if a live response differs from them.

## How an alert is produced

```
data/sample/*.csv  ->  seed.py  ->  SQLite (readings)  ->  analysis.py  ->  rules.py  ->  alerts table  ->  /api/alerts
 + traceability.csv      (quality                          baseline, quality,   8 rules
                          columns merged)                  day-level flags
```

1. **Seed.** `app/db/seed.py` reads `data/sample/manifest.json`, loads each profile's CSV, merges the quality
   sidecar (`traceability.csv`) so poor readings are known, then computes alerts for every day.
2. **Analyse.** `engine/analysis.py` makes one chronological pass. For each metric and day it records the valid
   value, the personal baseline (last 7 valid, non-flagged, comparable readings), the difference and a day-level
   flag. `engine/quality.py` decides what is valid. `engine/baseline.py` holds the baseline helpers.
3. **Rules.** `engine/rules.py` has one function per rule (HR-01, HR-02, SPO2-01, SLEEP-01, SLEEP-02, TEMP-01,
   DATA-01, DATA-02). Alerts are sorted most severe first, then newest first, and numbered `a1`, `a2`, ...
4. **Serve.** The routes only read the database, so responses are fast and identical every time.

Alerts are computed when the database is seeded, not on every request. After changing data or rules, run
`python -m app.db.seed` (or `./scripts/reset_demo.sh`).

## Folder map

```
app/
  main.py               app factory, CORS, auto-seed on first start
  config.py             settings from environment variables, optional .env, defaults
  errors.py             the single error shape
  utils.py              small helpers (timestamps, number formatting)
  db/
    schema.sql          tables: profile, readings, alerts (rebuilt by the seed)
    database.py         SQLite connection helper
    seed.py             loads the dataset and computes alerts (safe to re-run)
  engine/
    rules_config.py     ALL rule ids, names, severities, next steps, sources and thresholds
    quality.py          reading validity (missing, poor quality, skin temperature checks)
    baseline.py         time windows, comparable readings, rolling baseline
    analysis.py         per-day value, baseline, difference and flag table
    rules.py            the eight rules and the evaluate functions
    service.py          database to engine glue, stores and fetches alerts
  routes/               status, profile, readings, alerts, assistant (thin handlers)
  services/
    rag_adapter.py      calls rag/ask.py with a timeout and a safe fallback
    rag_stub.py         marked placeholder assistant used until rag/ask.py exists
    health.py           real checks behind /api/status
tests/                  pytest suite (see Tests)
```

## Settings

No configuration is needed. To change one, set an environment variable or copy `../.env.example` to `../.env`.
Priority: real environment variables, then `.env`, then the defaults in `app/config.py`. Restart after changes.

| Variable | Default | Purpose |
|----------|---------|---------|
| `ASTRO_ID` | `ASTRO-01` | which fictional astronaut the API serves (`ASTRO-02` is the other) |
| `ASTRO_DB_PATH` | `data/runtime/astro.db` | SQLite file |
| `ASTRO_SAMPLE_CSV` | `data/sample/readings.csv` | sample data location (the manifest is read from the same folder) |
| `CORS_ORIGINS` | `localhost` and `127.0.0.1` on ports 3000 and 3001 | frontend addresses allowed to call the API |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | where the local model server is checked |
| `OFFLINE_MODE` | `true` | the `offline_mode` flag on `/api/status` |
| `RAG_INDEX_DIR` | `rag/index` | where `meta.json` (document count) is read |
| `ASK_TIMEOUT_SECONDS` | `20` | wait for the model before falling back to retrieval-only |
| `ENV_FILE` | `.env` at the repo root | alternative `.env` file |

## The assistant

`POST /api/assistant/ask` takes `{"question": "...", "alert_id": "a1"}` (`alert_id` optional). The adapter in
`services/rag_adapter.py`:

- loads `rag/ask.py` if it exists, otherwise uses the marked placeholder in `rag_stub.py` (the log says
  `rag.ask not available`);
- calls `ask(question, alert)` in a worker thread and waits up to `ASK_TIMEOUT_SECONDS`;
- on timeout, exception or invalid output calls `retrieval_only(...)`, and forces `mode` to `retrieval_only`;
- always adds the disclaimer, so the endpoint never returns a 500 because of the model.

The exact contract for the RAG owner, with a checker script, is in [`../rag/INTERFACE.md`](../rag/INTERFACE.md).
If `ask()` needs extra Python packages, add them to `requirements.txt` (it runs inside this process).

## Common changes

**Change a threshold or wording.** Edit `app/engine/rules_config.py` only, then re-seed. Keep the rule names exact:
the frontend shows them. `temp_delta_threshold` must stay at or above the sensor accuracy plus noise margin or the
app refuses to start.

**Turn a rule off.** Set `"enabled": False` for it in `rules_config.py`.

**Add a rule.**
1. Add its entry to `RULES_CONFIG` in `rules_config.py` (name, severity, category, next step, source, numbers).
2. Write `def my_rule(series, analysis, i, cfg)` in `rules.py` returning `_alert(...)` or `None`, and add it to
   `RULE_FUNCS`.
3. Add normal, borderline and abnormal cases to `tests/test_rules.py`.
4. Re-seed, regenerate `../contract/examples/alerts.json` if the shape changed, and tell the frontend owner.

**Use different data.** Put the new files in `../data/sample/` in the same format (see
`../data/sample/README.md` and `DATA_SHEET.md`), update `manifest.json`, re-seed, and re-check
`tests/test_demo_scenario.py` against `expected_alerts.json`.

**Serve the other astronaut.** `ASTRO_ID=ASTRO-02 ./scripts/run_local.sh`.

**Change the database schema.** Edit `app/db/schema.sql`, delete `data/runtime/astro.db`, re-seed.

**Change the API shape.** It is a contract: agree it with the frontend owner first, update
`../contract/examples/` and `../docs/api-contract.md`, and keep `tests/test_contract.py` passing.

## Tests

```bash
./scripts/run_tests.sh        # or, from this folder: python -m pytest
```

| File | Covers |
|------|--------|
| `test_rules.py` | each rule: normal, borderline and abnormal inputs; ordering; disabled rules |
| `test_baseline.py` | baseline window, exclusions, time windows, sensor location, preflight baseline |
| `test_quality.py` | reading validity and the temperature threshold guard |
| `test_demo_scenario.py` | Sofia's dataset against her `expected_alerts.json` (days 20, 22, 26 and the clean profile) |
| `test_seed.py` | seeding both profiles, the quality sidecar, defaults, fallbacks |
| `test_endpoints.py` | readings, alerts, profile, second astronaut, error shape, CORS |
| `test_assistant.py` | answers, 404 and 422 errors, timeout and crash fallback, normalisation |
| `test_status.py` | real status checks |
| `test_contract.py` | live responses have exactly the fields in `contract/examples/` |
| `test_env_file.py` | `.env` loading and priority |

Tests use a temporary database, so they never touch `data/runtime/`.

## Docker

`docker compose up --build` from the repo root builds this folder with `Dockerfile`. The image holds only the
backend code; compose mounts `contract/`, `data/sample/`, `data/runtime/` and `rag/` into it. See
[`../docs/running-with-docker.md`](../docs/running-with-docker.md).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `no such column` or `table has no column` | The schema changed. Delete `data/runtime/astro.db` and re-seed. |
| `ASTRO_ID '...' is not in the dataset` | Use `ASTRO-01` or `ASTRO-02`, or fix `manifest.json`. |
| Browser shows a CORS error | Add the frontend address to `CORS_ORIGINS` and restart. |
| Port 8000 is taken | Start with `--port 8001` and point the frontend (`NEXT_PUBLIC_API_URL`) at it. |
| `/api/status` shows `llm: unavailable` | Start the model server (`ollama serve`) or fix `OLLAMA_URL`. |
| Log says `rag.ask not available` | Expected until `rag/ask.py` exists. If it exists, run `python rag/check_interface.py` to see why it fails. |
| `documents_indexed` is 0 | `rag/index/meta.json` is missing. The RAG owner writes it after indexing. |
| A test fails after editing sample data | `test_demo_scenario.py` compares against `data/sample/expected_alerts.json`. Update both on purpose. |
| A script says permission denied (macOS or Linux) | `chmod +x scripts/*.sh` |

## Conventions

- One error shape, UTC timestamps, lowercase `notice` / `watch` / `attention` in the API.
- `body_temp_c` is wearable **skin** temperature. Core temperature is a separate manual measurement and is never
  mixed with it.
- Every response that carries health data is labelled `SIMULATED`.
- No login: the server listens on the local machine only. See [`../docs/limitations.md`](../docs/limitations.md).
