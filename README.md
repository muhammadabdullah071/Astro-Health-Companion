# Astro-Health Companion

An offline, evidence-grounded astronaut health monitoring and decision-support prototype, built for the
NASA International Space Apps Challenge 2026 (challenge: **Health Monitoring Software**).

> **All data in this project is SIMULATED.** Decision support only, not a medical diagnosis.

## The problem

On long missions, far from Earth, astronauts face radiation, isolation and confinement, altered gravity and a
closed environment. These can bring immune changes, bone loss, cardiovascular events and behavioural-health
problems, and astronauts must notice many of these changes themselves. This prototype collects health
indicators, shows how they change over time, flags unusual changes with transparent rules, and lets the
astronaut ask an offline assistant why an alert appeared. Answers are built from a small library of trusted
scientific papers and show their sources.

## What it does

- **Dashboard:** heart rate, SpO2, sleep and skin temperature with 14-day trends and a daily summary.
- **Transparent alerts:** eight plain-English rules compare each astronaut with their own baseline. Every alert
  states which rule fired, the value, the baseline, the difference, the severity and a suggested next step.
- **Offline assistant:** explains an alert using only a local library of papers, with numbered citations. If the
  model is slow or unavailable it falls back to cited excerpts (retrieval-only mode).
- **Works offline:** database, rules, library, model and interface all run locally.
- **Honest labelling:** a SIMULATED badge and a disclaimer on every screen.

## Components

| Folder | Owner | What it holds |
|--------|-------|---------------|
| `frontend/` | Abdullah | Next.js interface: Dashboard, Health Alerts, AI Assistant, System Status |
| `backend/` | Elthiero | FastAPI + SQLite API, baseline and rules engine, assistant adapter, tests |
| `rag/` | Cesar | Source ingestion, local index, `ask()` with citations |
| `research/` | Ammara | Indicators, alert rules, curated sources |
| `data/` | Sofia | Simulated datasets, data sheet, generator |
| `tests/` | Shubhi | Cross-component and offline tests |
| `contract/examples/` | shared | One JSON example per API response (the contract) |
| `docs/` | shared | Architecture, API contract, limitations, Docker notes |

## Quick start (backend)

Needs Python 3.10 or newer. From the repo root:

```bash
./scripts/run_local.sh          # macOS / Linux
scripts\run_local.bat           # Windows
```

Then open <http://127.0.0.1:8000/docs>. The database is created and seeded on first start.

```bash
python scripts/smoke_test.py    # checks every endpoint of the running server
./scripts/run_tests.sh          # backend test suite
./scripts/reset_demo.sh         # rebuild the demo database (Windows: scripts\reset_demo.bat)
```

Docker is optional: `docker compose up --build` (see [docs/running-with-docker.md](docs/running-with-docker.md)).
Settings need no configuration; to change one, copy `.env.example` to `.env`.

The frontend has its own install and run commands in `frontend/`.

## The 60 second demo

The demo uses the fictional astronaut ASTRO-01 (30 days, newest reading is mission day 30):

| Mission day | What happens | Alert |
|-------------|--------------|-------|
| 1 to 7 | Calibration window, baseline not yet established | DATA-02 (hidden from the default view) |
| 20 | Heart rate 78 bpm against a baseline of 62 bpm (+16) | **HR-01**, WATCH |
| 22 | One poor-quality SpO2 reading (93%) | **DATA-01**, NOTICE (data quality, no health inference) |
| 26 | Sleep 5.4, 5.6 and 5.2 hours on three nights | **SLEEP-01**, NOTICE |

The astronaut asks "Why was this flagged?", the assistant answers from the local library with citations, and the
internet is switched off to show that everything still works.

## Alert rules

All thresholds are prototype workflow rules, not medical thresholds, and live in
`backend/app/engine/rules_config.py`.

| ID | Rule | Severity |
|----|------|----------|
| HR-01 | Resting heart rate above personal baseline (15 bpm or more) | WATCH |
| HR-02 | Persistent heart rate deviation (HR-01 on 2 consecutive days) | ATTENTION |
| SPO2-01 | SpO2 below personal baseline (3 points or more, 2 consecutive valid readings) | WATCH |
| SLEEP-01 | Sleep under 6 hours for 3 nights | NOTICE |
| SLEEP-02 | Sleep 1.5 hours or more below baseline for 3 consecutive nights | WATCH |
| TEMP-01 | Skin temperature 0.5 C or more above skin baseline on 2 consecutive comparable readings | WATCH |
| DATA-01 | Insufficient or unreliable data | NOTICE (data quality) |
| DATA-02 | Baseline not established (fewer than 7 usable days) | NOTICE (setup) |

Skin temperature is not core temperature, and the two are never mixed.

## API

| Method | Endpoint | Returns |
|--------|----------|---------|
| GET | `/api/status` | backend, offline flag, model state, documents indexed, last data update |
| GET | `/api/profile` | astronaut and mission day |
| GET | `/api/readings?days=14` | readings, oldest first |
| GET | `/api/alerts?days=14` | alerts from the last N days, most severe first |
| POST | `/api/assistant/ask` | answer, mode, citations and disclaimer |

Full field descriptions: [docs/api-contract.md](docs/api-contract.md). Example responses: `contract/examples/`.

## Data

Two fictional profiles, 30 days each, generated reproducibly with a fixed seed. Sources, parameters and limits are
in [data/sample/DATA_SHEET.md](data/sample/DATA_SHEET.md). NASA OSDR was used for research context only and none of
its values appear in the generated files.

## Documentation

- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Limitations](docs/limitations.md)
- [Running with Docker](docs/running-with-docker.md)
- [Contributing](CONTRIBUTING.md)

## Limitations and ethics

This is decision support, not a medical device. The data is simulated, the library is small, and the numeric rules
are unvalidated prototype rules. We do not claim clinical validation, diagnostic performance, real astronaut data or
proven prediction of any condition. Read [docs/limitations.md](docs/limitations.md) before drawing any conclusion.

## AI tools and credits

- Parts of the backend code, tests and documentation were drafted with Claude (Anthropic) and reviewed, run and
  tested by the team.
- The assistant runs a local model through Ollama and local embeddings. Model names: see `rag/`.
- Scientific sources are credited in the assistant's citations and in `research/`.
- NASA OSDR was consulted for context only. No real astronaut data was used.

## Team

Abdullah (team lead, frontend), Elthiero (backend, integration), Cesar (local model and RAG), Ammara (medical
research, rules, UX), Sofia (data), Shubhi (testing and QA).
