# Elthiero's checklists

Tick each box when the check is true, not when you think it is. "In package" tells you what
already exists; your job is to verify it, adapt it to the real inputs, and demo it at the checkpoint.
Times are Rwanda time. Checkpoints: CP0 12 Nov night, CP1 13 Nov night, CP2 14 Nov midday,
CP3 14 Nov night, CP4 15 Nov midday.

---------------------------------------------------------------------

## Step 0. Setup (12 Nov, before anything else)

In package: whole backend, tests, scripts.

- [ ] Python 3.10 or newer installed (`python3 --version`)
- [ ] Repo cloned, branch `feature/backend` created, package folders copied in
- [ ] `./scripts/run_local.sh` (or `.bat`) starts the server without errors
- [ ] http://127.0.0.1:8000/docs opens in the browser
- [ ] `./scripts/run_tests.sh` shows 81 passed
- [ ] `python scripts/smoke_test.py` shows ALL CHECKS PASSED
- [ ] Pull request opened and Abdullah told the API is live
- [ ] `git status` shows no `.venv`, `__pycache__`, `.env` or `data/runtime/astro.db` (the ignore files work)

## Step 1. Mock and contract live (12 Nov night, CP0)

In package: the real API already serves contract-shaped data; contract/examples has every shape.

- [ ] Abdullah can fetch /api/readings, /api/alerts, /api/status and /api/profile from his machine
- [ ] CORS works from http://localhost:3000 (no browser CORS error)
- [ ] contract/examples copied or linked so Abdullah can use them as his mock JSON
- [ ] docs/api-contract.md read by Abdullah; any field he wants changed is discussed now
- [ ] Contract v1 declared frozen in the group chat

## Step 2. Agreements in the group chat (12 Nov night)

In package: docs/PLACEHOLDERS.md has the text to send.

- [ ] Error shape agreed: {"error": {"code", "message"}}
- [ ] Severity values agreed: notice, watch, attention (lowercase)
- [ ] Profile response fields agreed with Abdullah
- [ ] Cesar received the rag/ask.py interface (ask, retrieval_only, meta.json) and confirmed it
- [ ] Ammara received the request for rules in a fixed format: rule, metric, condition, threshold, severity, next step, source
- [ ] Sofia told the exact CSV columns: timestamp, heart_rate_bpm, spo2_pct, sleep_hours, body_temp_c (UTC, ISO)
- [ ] Shubhi told where tests live (backend/tests) and how to run them

## Step 3. Database and seed (13 Nov)

In package: db/schema.sql, db/seed.py, data/sample/readings.csv, data/generate_placeholder_data.py.

- [ ] `python -m app.db.seed` prints readings (26) and alerts (9) counts
- [ ] Running the seed twice gives the same result (idempotent)
- [ ] Timestamps in the database are UTC with a trailing Z
- [ ] Database file is created at data/runtime/astro.db and is git-ignored
- [ ] Readings table has the quality columns (hr_quality, spo2_quality, sleep_source, temp_sensor_location, temp_device_id, temp_contact_quality, temp_dropout)
- [ ] A CSV with only the 5 core columns still seeds (quality columns default)
- [ ] Poor quality readings are stored, not dropped
- [ ] `body_temp_c` is understood as SKIN temperature; core temperature is NOT stored in the readings table
- [ ] Sofia's CSV (when delivered) seeds with `--csv path`, or you reported the format problem to her
- [ ] Demo scenario holds after re-seeding: day 20 HR-01, days 24 to 26 SLEEP-01, days 1 to 7 clean (test_demo_scenario.py)

## Step 4. Baseline engine (13 Nov, CP1)

In package: engine/baseline.py, engine/analysis.py, engine/quality.py, tests/test_baseline.py, tests/test_quality.py.

- [ ] Baseline = mean of the last 7 valid, non-flagged readings; fewer than 7 gives "not established"
- [ ] Readings that triggered an alert are left out of later baselines
- [ ] Poor quality and missing readings are left out
- [ ] Temperature baseline is per time window and per sensor location
- [ ] Preflight baseline hook works (`PREFLIGHT_BASELINE`)
- [ ] Ammara confirmed assumptions 1 to 3 in docs/PLACEHOLDERS.md
- [ ] Baseline and quality tests pass

## Step 5. Rules engine (14 Nov morning)

In package: engine/rules_config.py, engine/rules.py, tests/test_rules.py.

- [ ] Eight rules present with Ammara's exact ids, names, severities, next steps and sources
- [ ] Every number lives in rules_config.py (nothing hard-coded in rules.py)
- [ ] Each rule has normal, borderline and abnormal tests
- [ ] TEMP-01 threshold (`temp_delta_threshold`) reviewed by Sofia and Ammara against the sensor accuracy
- [ ] DATA-01 and DATA-02 stay separate from physiological alerts (category field)
- [ ] No personalised alert fires while the baseline is not established (DATA-02 instead); SLEEP-01 still can
- [ ] Alerts are evaluated on every day, most severe first, ids a1, a2, ...
- [ ] Shubhi reviewed the rule tests and added her cases
- [ ] A rule Ammara drops is set to "enabled": False (not deleted) until the team agrees

## Step 6. Real endpoints (14 Nov morning, CP2)

In package: routes/readings.py, profile.py, alerts.py, tests/test_endpoints.py, test_contract.py.

- [ ] /api/readings?days=14 returns 14 rows oldest first, with data_label SIMULATED
- [ ] /api/readings?days=0 and /api/alerts?days=0 return the 422 error shape
- [ ] /api/alerts returns the new fields (rule_id, category, unit, delta, baseline_status, next_step, source, data_quality, data_label, temperature fields)
- [ ] Default alerts are HR-01 (day 20) and SLEEP-01 (day 26); `?days=26` also shows DATA-02 calibration alerts
- [ ] Abdullah agreed the additive alert fields and the new `message` wording
- [ ] Contract tests pass (live fields equal contract/examples)
- [ ] Abdullah switched off mock mode and the dashboard shows real data with alert markers (CP2 demo)

## Step 7. Assistant endpoint (14 Nov afternoon, CP3)

In package: routes/assistant.py, services/rag_adapter.py, rag_stub.py, tests/test_assistant.py.

- [ ] POST with alert_id returns answer, mode, citations, disclaimer
- [ ] Unknown alert_id returns 404 with the error shape
- [ ] Empty question returns 422
- [ ] Question with no alert gets the honest limitation answer
- [ ] Cesar's rag/ask.py added; `ask` and `retrieval_only` found automatically (check the server log has no "rag.ask not available" line)
- [ ] Timeout test: with the model stopped or slow, the answer arrives within about 20 s as retrieval_only
- [ ] A crash inside ask() never produces a 500
- [ ] Disclaimer text is present on every answer
- [ ] Decision made with Cesar and Ammara: llm mode or retrieval-only mode for the demo (decide by CP3)
- [ ] Placeholder citations are gone from the demo path (real papers only)

## Step 8. Real status endpoint (14 Nov afternoon)

In package: routes/status.py, services/health.py, tests/test_status.py.

- [ ] backend shows "ok"
- [ ] Stopping Ollama changes llm to "unavailable"; starting it changes it to "ready"
- [ ] documents_indexed matches the real number (Cesar writes rag/index/meta.json)
- [ ] last_data_update equals the newest reading
- [ ] offline_mode is true in the demo environment (OFFLINE_MODE)
- [ ] The status call returns quickly (under about 1.5 s) even when Ollama is off

## Step 9. Packaging and offline test (15 Nov morning, CP4)

In package: scripts, Dockerfile, docker-compose.yml, smoke_test.py, docs/running-with-docker.md.

- [ ] requirements.txt versions pinned (they are) and still correct
- [ ] Clean folder or clean machine: `run_local` works from scratch
- [ ] Windows: `scripts\run_local.bat` tested on a Windows machine
- [ ] `reset_demo` restores the demo state in seconds
- [ ] Embedding model and Ollama model downloaded while online and cached on the demo laptop
- [ ] Wi-Fi OFF: start the app, run `python scripts/smoke_test.py`, all checks pass
- [ ] Wi-Fi OFF: restart the app once and repeat the smoke test
- [ ] Docker path tested once with Wi-Fi off, started with `docker compose up` (only if the team will use Docker)
- [ ] If Cesar's rag/ask.py needs extra packages, they are in backend/requirements.txt and the image was rebuilt
- [ ] Shubhi ran the official offline test and her report has no open blocker
- [ ] README run steps written and checked by someone who did not write them

## Step 10. Feature freeze and handoff (15 Nov midday, CP4)

- [ ] Only blocker fixes since CP3
- [ ] All pull requests merged; main is demo-ready
- [ ] `./scripts/run_tests.sh` passes on main
- [ ] Final commit tagged (for example v1.0-submission)
- [ ] Repo link sent to Ammara for the portal
- [ ] No large files, PDFs, models or database in git
- [ ] You can explain your module and how it connects to the others in two minutes

---------------------------------------------------------------------

## Daily routine

- [ ] Pull and merge small pull requests at least twice a day; never push to main
- [ ] Post in the group chat after each step: what works, what is next, what blocks you
- [ ] Anything stuck for 30 minutes: post a screenshot, it becomes a board task

## Demo day (15 Nov) checklist

- [ ] Laptop charged, charger packed, models cached
- [ ] `reset_demo` run just before the demo
- [ ] Server started, smoke test green
- [ ] Wi-Fi switched off live during the demo (step 3 of the script)
- [ ] Backup recording of the full demo flow saved on the laptop
- [ ] You know the answers to: Is this real data? Why rules and not ML? What if the model is slow?
