# Astro-Health Companion

> **Offline health awareness and evidence-grounded decision support for crews beyond Earth’s reach.**

[![Live frontend](https://img.shields.io/badge/demo-live-8b5cf6?logo=vercel&logoColor=white)](https://astro-health-companion.vercel.app/)
[![API status](https://img.shields.io/badge/API-live-22c55e?logo=fastapi&logoColor=white)](https://api.astrohealth.us/api/status)
[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/frontend-Next.js-000000?logo=next.js&logoColor=white)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

Astro-Health Companion is an offline-capable astronaut health monitoring and decision-support prototype built for the **NASA International Space Apps Challenge 2026 — Health Monitoring Software** challenge.

It tracks simulated vital-sign trends against a personal baseline, explains transparent alerts, and answers health-awareness questions from a curated local scientific library. The system is designed for missions where communication with Earth may be delayed or unavailable.

> **Important:** Every value in this repository is simulated. This is a research/demo prototype, not a medical device or diagnostic system. Its rules are workflow rules, not validated clinical thresholds.

## Live deployments

| Experience | URL | Description |
|---|---|---|
| Web application | [astro-health-companion.vercel.app](https://astro-health-companion.vercel.app/) | Interactive landing page, dashboard, alerts, assistant and system-status screens |
| Backend health | [api.astrohealth.us/api/status](https://api.astrohealth.us/api/status) | Live FastAPI status response |
| API documentation | [api.astrohealth.us/docs](https://api.astrohealth.us/docs) | Interactive Swagger/OpenAPI documentation |
| OpenAPI schema | [api.astrohealth.us/openapi.json](https://api.astrohealth.us/openapi.json) | Machine-readable API definition |

The deployed web demo includes a self-contained frontend API layer so it can be explored without a backend connection. The repository also contains the production-shaped FastAPI + SQLite service and the offline retrieval pipeline.

## Demo

Watch the product walkthrough to see the landing page, health dashboard, transparent alerts, evidence-grounded assistant and offline status flow in action.

<p align="center">
  <video src="assets/astro-health-companion-demo.mp4" controls width="850">
    Your browser does not support embedded video. <a href="assets/astro-health-companion-demo.mp4">Watch the demo video</a>.
  </video>
</p>

**[Download or watch the demo video](assets/astro-health-companion-demo.mp4)**

## Why it exists

During long-duration missions, crews may need to interpret changes in heart rate, oxygen saturation, sleep and temperature without immediate clinical support. Astro-Health Companion makes that workflow explicit:

1. **Collect readings** locally.
2. **Compare readings with the astronaut’s own baseline**, rather than a generic population threshold.
3. **Raise explainable alerts** that name the rule, value, baseline, severity and next step.
4. **Explain the alert with cited evidence** from a local scientific library.

## Product capabilities

- **Health dashboard** — 14-day trends for resting heart rate, SpO2, sleep and wearable skin temperature.
- **Personal baselines** — rolling baselines are calculated from recent valid, comparable readings.
- **Transparent alerts** — eight plain-English rules produce `notice`, `watch` or `attention` alerts.
- **Evidence-grounded assistant** — answers use local sources and numbered citations.
- **Retrieval-only fallback** — the assistant remains useful when the local LLM is slow or unavailable.
- **Offline-first operation** — SQLite, alert logic, source metadata and the interface can run locally.
- **Installable frontend** — the Next.js app includes a basic service worker and web manifest.
- **Honest safety labelling** — simulated data and the decision-support disclaimer are surfaced throughout the experience.

## System architecture

```text
                         ┌──────────────────────────┐
                         │ Next.js frontend          │
                         │ dashboard / alerts / UX  │
                         └────────────┬─────────────┘
                                      │ API contract v1
                         ┌────────────▼─────────────┐
                         │ FastAPI backend           │
                         │ routes + SQLite           │
                         └──────┬─────────┬──────────┘
                                │         │
                 readings/alerts│         │assistant questions
                                │         ▼
                         ┌──────▼───┐ ┌─────────────┐
                         │ Rules and │ │ Local RAG   │
                         │ baselines │ │ + Ollama    │
                         └──────┬────┘ └──────┬──────┘
                                │             │
                         ┌──────▼─────────────▼──────┐
                         │ Simulated datasets +       │
                         │ curated scientific sources │
                         └───────────────────────────┘
```

### Repository map

| Path | Purpose |
|---|---|
| [`frontend/`](frontend/) | Next.js 15 App Router frontend, TypeScript, React, Three.js and PWA assets |
| [`backend/`](backend/) | FastAPI service, SQLite persistence, baseline analysis, alert rules and API tests |
| [`rag/`](rag/) | Curated source metadata, ingestion, retrieval and Ollama integration |
| [`data/sample/`](data/sample/) | Reproducible simulated readings, manifests, quality data and expected alerts |
| [`contract/examples/`](contract/examples/) | JSON response examples used as the API contract |
| [`docs/`](docs/) | Architecture, API contract, limitations and Docker guidance |
| [`scripts/`](scripts/) | Local run, test, smoke-test and demo-reset helpers |
| [`research/`](research/) | Research ownership and domain context |
| [`tests/`](tests/) | Cross-component ownership and test organization |

## Alert rules

Rules are defined in [`backend/app/engine/rules_config.py`](backend/app/engine/rules_config.py). They are prototype workflow rules and should not be interpreted as clinical cut-offs.

| ID | Meaning | Severity |
|---|---|---|
| `HR-01` | Resting heart rate is at least 15 bpm above personal baseline | `watch` |
| `HR-02` | Heart-rate deviation persists for two consecutive days | `attention` |
| `SPO2-01` | SpO2 is at least 3 points below baseline across two valid readings | `watch` |
| `SLEEP-01` | Sleep is below six hours for three nights | `notice` |
| `SLEEP-02` | Sleep is at least 1.5 hours below baseline for three nights | `watch` |
| `TEMP-01` | Wearable skin temperature is at least 0.5 °C above baseline twice | `watch` |
| `DATA-01` | Reading quality or coverage is insufficient, including stale data when enabled | `notice` |
| `DATA-02` | A personal baseline has not been established | `notice` |

Skin temperature is explicitly treated as a wearable skin measurement; it is never presented as core temperature.

## API

The FastAPI service exposes the following contract:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/status` | Backend, offline mode, LLM state, indexed documents and latest data time |
| `GET` | `/api/profile` | Fictional astronaut profile and mission information |
| `GET` | `/api/readings?days=14` | Recent readings, oldest first; `days` is 1–90 |
| `GET` | `/api/alerts?days=14` | Recent alerts, ordered by severity and recency |
| `POST` | `/api/assistant/ask` | Cited answer, mode, sources and safety disclaimer |
| `POST` / `GET` | `/api/core-temperature` | Manual core-temperature entries, stored apart from skin readings and never used by rules |

Every response containing health data is labelled `SIMULATED`. Errors use a consistent shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "..."
  }
}
```

See the complete field definitions in [`docs/api-contract.md`](docs/api-contract.md) and example payloads in [`contract/examples/`](contract/examples/).

## Quick start

### Option A: run the FastAPI backend on Windows

From the repository root:

```powershell
scripts\run_local.bat
```

The script creates `backend\.venv`, installs the backend dependencies and starts the API at [http://127.0.0.1:8000](http://127.0.0.1:8000).

Open the interactive API documentation at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### Option B: run the backend manually

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The database is created and seeded automatically on first startup.

### Run the Next.js frontend

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). For a production build:

```powershell
npm run build
npm start
```

### Option C: Docker Compose

Run the backend only:

```bash
docker compose up --build
```

Run the backend and frontend:

```bash
docker compose --profile full up --build
```

Docker Compose exposes the backend on port `8000` and the frontend on port `3000`. Ollama is intentionally not containerized; when enabled, the backend reaches a host Ollama server through `host.docker.internal`. See [`docs/running-with-docker.md`](docs/running-with-docker.md).

## Configuration

The backend works with built-in defaults. To customize it:

```powershell
Copy-Item .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `ASTRO_ID` | `ASTRO-01` | Fictional astronaut profile (`ASTRO-01` or `ASTRO-02`) |
| `ASTRO_DB_PATH` | `data/runtime/astro.db` | SQLite database location |
| `ASTRO_SAMPLE_CSV` | `data/sample/readings.csv` | Seed readings file |
| `CORS_ORIGINS` | Local ports 3000/3001 | Comma-separated frontend origins |
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Local Ollama server |
| `OLLAMA_MODEL` | environment-dependent | Model used for generated answers |
| `OFFLINE_MODE` | `true` | Offline status flag exposed by the API |
| `RAG_INDEX_DIR` | `rag/index` | Retrieval metadata directory |
| `ASK_TIMEOUT_SECONDS` | `20` | Model timeout before retrieval-only fallback |

## Data and retrieval

The demo contains two fictional astronaut profiles with 30 days of reproducible readings. The data generator uses a fixed seed, and the quality sidecar makes unreliable readings explicit. NASA OSDR informed research context only; no real astronaut data is included.

The retrieval library contains nine curated sources covering spaceflight physiology, Earth-independent medical operations, sleep, immunity, radiation and musculoskeletal health. The assistant:

- retrieves only from the local library;
- includes source titles, links and excerpts;
- distinguishes LLM answers from `retrieval_only` answers;
- avoids diagnosing conditions from wearable data;
- refuses unsupported questions instead of fabricating evidence.

Refresh the local index and run the grounding benchmark from the repository root:

```bash
python -m rag.ingest
python -m rag.test_10_questions
python -m rag.test_10_questions --llm
```

## Testing and verification

Run the backend test suite:

```bash
./scripts/run_tests.sh
```

On Windows, activate the backend environment and run:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

With the API running, check every endpoint:

```bash
python scripts/smoke_test.py
```

Reset and reseed the demo database when changing rules or sample data:

```powershell
scripts\reset_demo.bat
```

The test suite covers rules, baselines, data quality, seed behavior, endpoint validation, assistant fallbacks, API contract shape, status checks and the end-to-end demo scenario.

## Documentation

- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Limitations and ethics](docs/limitations.md)
- [Docker guide](docs/running-with-docker.md)
- [Backend guide](backend/README.md)
- [RAG and scientific library](rag/README.md)
- [Contributing](CONTRIBUTING.md)

## Limitations and responsible use

- All readings and profiles are simulated.
- Alert thresholds are not clinically validated.
- The source library is intentionally small.
- The assistant is not a doctor and does not provide diagnosis or emergency guidance.
- A healthy or clean result does not rule out a medical problem.
- There is no authentication or multi-user access control in this prototype.
- The frontend and backend can run as separate applications; production deployments should configure their integration and CORS policy explicitly.

Read [`docs/limitations.md`](docs/limitations.md) before using the project for research or demonstrations.

## Team

| Contributor | Focus |
|---|---|
| Abdullah | Team lead, frontend and documentation |
| Elthiero | Backend, APIs and integration |
| Cesar | Local AI and retrieval pipeline |
| Ammara | Medical research, indicators and alert rules |
| Sofia | Data exploration and simulated datasets |
| Shubhi | Testing and quality assurance |

## License and attribution

This repository does not currently include a license file. If you plan to redistribute or build on the project, add an explicit license and confirm the usage rights for any included research metadata and third-party assets.

Built for the **NASA International Space Apps Challenge 2026**.
