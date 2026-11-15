# Astro-Health Companion

> Offline health awareness and evidence-grounded decision support for crews beyond Earth’s reach.

[![Live frontend](https://img.shields.io/badge/Frontend-Live-8b5cf6?logo=vercel&logoColor=white)](https://astro-health-companion.vercel.app/)
[![Live backend](https://img.shields.io/badge/Backend-Live-009688?logo=fastapi&logoColor=white)](https://api.astrohealth.us/)
[![API status](https://img.shields.io/badge/API-Status-22c55e?logo=fastapi&logoColor=white)](https://api.astrohealth.us/api/status)

Astro-Health Companion is an offline-capable astronaut health monitoring and decision-support prototype built for the **NASA International Space Apps Challenge 2026 — Health Monitoring Software** challenge.

It tracks simulated health trends against personal baselines, explains alerts with transparent rules, and answers health-awareness questions using a curated local scientific library.

> **Important:** All data is simulated. This project is for research and demonstration only. It is not a medical device and does not provide medical diagnoses.

## Live project

| Resource | Link |
|---|---|
| **Frontend application** | [astro-health-companion.vercel.app](https://astro-health-companion.vercel.app/) |
| **Backend API** | [api.astrohealth.us](https://api.astrohealth.us/) |
| **API documentation** | [Swagger UI](https://api.astrohealth.us/docs) |
| **API status** | [Live status](https://api.astrohealth.us/api/status) |
| **Demo video** | [Watch the project demo](https://github.com/muhammadabdullah071/Astro-Health-Companion/raw/refs/heads/main/assets/astro-health-companion-demo.mp4) |

## Features

- **Health dashboard** — View heart rate, SpO2, sleep and wearable skin-temperature trends.
- **Personal baselines** — Compare readings with the astronaut’s recent valid readings.
- **Transparent alerts** — Every alert identifies the rule, measurement, baseline, severity and suggested next step.
- **Evidence-grounded assistant** — Ask why an alert appeared and receive cited sources.
- **Offline fallback** — Retrieval-only answers remain available when the local language model is unavailable.
- **Simulated-data labelling** — Health data and decision-support boundaries are clearly identified.

## How it works

```text
Simulated readings
        ↓
SQLite database
        ↓
Quality checks and personal baselines
        ↓
Transparent alert rules
        ↓
Local scientific retrieval and cited explanations
```

## Technology

- **Frontend:** Next.js 15, React, TypeScript, Three.js
- **Backend:** FastAPI, Python 3.10+, SQLite
- **Retrieval:** Local Python RAG pipeline with optional Ollama integration
- **Deployment:** Vercel frontend, FastAPI backend, Docker Compose for local deployment

## Repository structure

| Directory | Purpose |
|---|---|
| [`frontend/`](frontend/) | Next.js web application |
| [`backend/`](backend/) | FastAPI service, database and alert engine |
| [`rag/`](rag/) | Scientific source ingestion and retrieval |
| [`data/sample/`](data/sample/) | Reproducible simulated readings |
| [`contract/examples/`](contract/examples/) | API response examples |
| [`docs/`](docs/) | Architecture, API contract and deployment notes |
| [`scripts/`](scripts/) | Local run, test and demo utilities |

## Run locally

### Backend

On Windows, run from the repository root:

```powershell
scripts\run_local.bat
```

The API starts at [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

To run it manually:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### Docker

```bash
docker compose up --build
```

To run the backend and frontend together:

```bash
docker compose --profile full up --build
```

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/status` | Service health, offline mode and indexed sources |
| `GET` | `/api/profile` | Current fictional astronaut profile |
| `GET` | `/api/readings?days=14` | Recent health readings |
| `GET` | `/api/alerts?days=14` | Recent transparent alerts |
| `POST` | `/api/assistant/ask` | Evidence-grounded assistant response |
| `GET` / `POST` | `/api/core-temperature` | Separate manual core-temperature records |

See the full contract in [`docs/api-contract.md`](docs/api-contract.md).

## Testing

```bash
./scripts/run_tests.sh
```

On Windows:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest
```

## Limitations

- All readings and profiles are fictional and simulated.
- Alert thresholds are prototype workflow rules, not clinically validated thresholds.
- The assistant is not a doctor and must not be used for diagnosis or emergency decisions.
- The project does not currently include authentication or multi-user access control.

For more information, see [`docs/limitations.md`](docs/limitations.md).

## Team

Abdullah · Elthiero · Cesar · Ammara · Sofia · Shubhi

Built for the **NASA International Space Apps Challenge 2026**.
