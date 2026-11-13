# Astro-Health Companion: API Reference (contract v1)

Backend: FastAPI + SQLite, runs locally with no internet. All data is **SIMULATED**.
Decision support only, not a medical diagnosis.

- Base URL in development: `http://localhost:8000`
- Interactive docs while the server runs: `http://127.0.0.1:8000/docs`
- Source of truth for the shapes: `contract/examples/` (a test fails if a live response differs)
- Changes to field names need Abdullah and Elthiero to agree and a message in the group chat

The examples below were captured from the running backend with the placeholder sample data.
Exact numbers change when Sofia's data replaces it. The field names do not.

## Summary

| Method | Endpoint | Returns |
|--------|----------|---------|
| GET | `/api/status` | System health: backend, offline flag, model state, documents indexed, last data update |
| GET | `/api/profile` | Demo astronaut and mission day |
| GET | `/api/readings?days=14` | Health readings over time, oldest first |
| GET | `/api/alerts` | Active alerts, most severe first |
| POST | `/api/assistant/ask` | Answer with citations for a question, optionally about one alert |

## Conventions

- All timestamps are UTC ISO 8601 with a trailing `Z`.
- Every response that carries health data includes or implies `data_label: "SIMULATED"`.
- Every error uses the same shape (see Errors at the end).
- Field names are lowercase with underscores.

---

## GET /api/status

Used by the Status screen and the offline badge. This endpoint always answers, even when something is down.

```json
{
  "backend": "ok",
  "offline_mode": true,
  "llm": "ready",
  "documents_indexed": 12,
  "last_data_update": "2026-11-14T08:00:00Z",
  "data_label": "SIMULATED"
}
```

| Field | Meaning |
|-------|---------|
| `backend` | `ok` or `error` (the database answers a simple query) |
| `offline_mode` | From the `OFFLINE_MODE` setting, default `true` |
| `llm` | `ready` or `unavailable`, checked against the local model server |
| `documents_indexed` | Read from Cesar's `rag/index/meta.json`; `0` until that file exists |
| `last_data_update` | Timestamp of the newest reading |
| `data_label` | Always `SIMULATED` |

The example shows the model running with 12 papers indexed. With no model server and no index, the backend returns `"llm": "unavailable"` and `"documents_indexed": 0`.

---

## GET /api/profile

Proposal: the guide does not define this shape, so agree it with Abdullah.

```json
{
  "id": "astro-demo-1",
  "name": "Demo Astronaut A",
  "mission": "Simulated long-duration mission",
  "mission_day": 143,
  "baseline_window_days": 7,
  "data_label": "SIMULATED"
}
```

| Field | Meaning |
|-------|---------|
| `id`, `name`, `mission` | Demo astronaut details |
| `mission_day` | Computed from the mission start date and the newest reading |
| `baseline_window_days` | Days used for the personal baseline (7) |
| `data_label` | Always `SIMULATED` |

---

## GET /api/readings?days=14

Query parameter `days`: 1 to 90, default 14. Readings are the last N counted back from the newest reading (not the wall clock), oldest first, so the demo looks the same on any day.

The full response has 14 readings. This excerpt shows the last 3:

```json
{
  "data_label": "SIMULATED",
  "readings": [
    {
      "timestamp": "2026-11-12T08:00:00Z",
      "heart_rate_bpm": 62,
      "spo2_pct": 96,
      "sleep_hours": 5.7,
      "body_temp_c": 36.7
    },
    {
      "timestamp": "2026-11-13T08:00:00Z",
      "heart_rate_bpm": 62,
      "spo2_pct": 97,
      "sleep_hours": 5.5,
      "body_temp_c": 36.8
    },
    {
      "timestamp": "2026-11-14T08:00:00Z",
      "heart_rate_bpm": 78,
      "spo2_pct": 96,
      "sleep_hours": 5.8,
      "body_temp_c": 36.7
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `timestamp` | UTC time of the reading |
| `heart_rate_bpm` | Heart rate, beats per minute |
| `spo2_pct` | Oxygen saturation, percent |
| `sleep_hours` | Sleep, hours |
| `body_temp_c` | Body temperature, degrees Celsius |

---

## GET /api/alerts

Active alerts for the newest reading, most severe first. Ids are `a1`, `a2`, ... in that order.

```json
{
  "alerts": [
    {
      "id": "a1",
      "rule": "Resting heart rate above personal baseline",
      "severity": "watch",
      "metric": "heart_rate_bpm",
      "value": 78,
      "baseline": 62.3,
      "timestamp": "2026-11-14T08:00:00Z",
      "message": "Heart rate is 16 bpm above your 7-day baseline."
    },
    {
      "id": "a2",
      "rule": "Sleep under 6 hours for 3 nights in a row",
      "severity": "notice",
      "metric": "sleep_hours",
      "value": 5.8,
      "baseline": 6.4,
      "timestamp": "2026-11-14T08:00:00Z",
      "message": "Sleep has been under 6 hours for 3 nights in a row."
    }
  ]
}
```

| Field | Meaning |
|-------|---------|
| `id` | Alert id, used as `alert_id` when asking the assistant |
| `rule` | Plain-English name of the rule that fired |
| `severity` | `notice`, `watch` or `attention` |
| `metric` | Which reading triggered it |
| `value` | The measured value |
| `baseline` | The astronaut's own 7-day baseline, or `null` when there is not enough history |
| `timestamp` | When the triggering reading was taken |
| `message` | Human-readable explanation |

A normal day returns `{ "alerts": [] }`.

---

## POST /api/assistant/ask

Explains an alert, or answers a health question, using only the local scientific library.

Request body:

```json
{
  "question": "Why was this flagged?",
  "alert_id": "a1"
}
```

| Field | Rules |
|-------|-------|
| `question` | Required, 1 to 1000 characters |
| `alert_id` | Optional. If given and unknown, the API returns a 404 |

Response (captured with the placeholder assistant, so the text and sources are marked PLACEHOLDER):

```json
{
  "answer": "[PLACEHOLDER ANSWER] Heart rate is 16 bpm above your 7-day baseline. The rule that fired was 'Resting heart rate above personal baseline'. Possible contributing factors will come from the scientific library [1][2]. Suggested next step: Rest, re-measure after 15 minutes, and log how you feel. Follow mission medical procedure if it stays high.",
  "mode": "llm",
  "citations": [
    {
      "title": "PLACEHOLDER source 1 (replace with a paper from Ammara's list)",
      "source": "NASA",
      "url": "https://example.org/placeholder-1",
      "excerpt": "Placeholder excerpt used only for UI and integration development."
    },
    {
      "title": "PLACEHOLDER source 2 (replace with a paper from Ammara's list)",
      "source": "PubMed",
      "url": "https://example.org/placeholder-2",
      "excerpt": "Placeholder excerpt used only for UI and integration development."
    }
  ],
  "disclaimer": "Decision support only - not a medical diagnosis."
}
```

| Field | Meaning |
|-------|---------|
| `answer` | The answer text; may contain numbered references like `[1]` |
| `mode` | `llm` or `retrieval_only`. Show a tag in the UI when it is `retrieval_only` |
| `citations` | Sources used: `title`, `source`, `url`, `excerpt` |
| `disclaimer` | Always present: decision support only |

Behaviour to design the UI around:

- If the model is slow (over 20 seconds), crashes or returns bad output, the endpoint still returns a normal `200` response in `retrieval_only` mode. It never returns a `500` because of the model.
- With no `alert_id` and no supporting evidence, the answer says it cannot answer and `citations` is empty:

```json
{
  "answer": "I cannot answer that from my sources.",
  "mode": "retrieval_only",
  "citations": [],
  "disclaimer": "Decision support only - not a medical diagnosis."
}
```

- Until Cesar's `rag/ask.py` exists, the answer and citations are clearly marked PLACEHOLDER.

---

## Errors (all endpoints)

Every error has this shape:

```json
{ "error": { "code": "NOT_FOUND", "message": "Alert not found." } }
```

| Status | `code` | When | Real example response |
|--------|--------|------|-----------------------|
| 404 | `NOT_FOUND` | Unknown `alert_id` or unknown route | `{"error": {"code": "NOT_FOUND", "message": "Alert not found."}}` |
| 405 | `METHOD_NOT_ALLOWED` | Wrong HTTP method on a route | |
| 422 | `VALIDATION_ERROR` | Bad input, such as `days=0` or an empty question | `{"error": {"code": "VALIDATION_ERROR", "message": "Invalid request: query.days."}}` |
| 500 | `INTERNAL_ERROR` | Unexpected server error | |

More examples:

- Empty question, status 422: `{"error": {"code": "VALIDATION_ERROR", "message": "Invalid request: question."}}`
- Unknown route, status 404: `{"error": {"code": "NOT_FOUND", "message": "Not Found"}}`

---

## Quick checks

- Run the server: `./scripts/run_local.sh` (Windows: `scripts\run_local.bat`)
- Try every endpoint in the browser: `http://127.0.0.1:8000/docs`
- Automated check of a running server: `python scripts/smoke_test.py`
- Contract tests: `./scripts/run_tests.sh`
