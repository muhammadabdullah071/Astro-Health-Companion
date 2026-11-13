# API contract v1

Base URL in development: http://localhost:8000. The example files in `contract/examples/`
are the source of truth, and `backend/tests/test_contract.py` fails if a live response
has different fields. Changes need Abdullah and Elthiero to agree and a message in the group chat.

## GET /api/status
`contract/examples/status.json`
Fields: backend ("ok" | "error"), offline_mode, llm ("ready" | "unavailable"),
documents_indexed, last_data_update (newest reading, UTC), data_label.

## GET /api/profile
`contract/examples/profile.json` (proposal: the guide does not define this shape)
Fields: id, name, mission, mission_day, baseline_window_days, data_label.

## GET /api/readings?days=14
`contract/examples/readings.json`
`days` is 1 to 90. Readings are the last N relative to the newest reading, oldest first.
Fields: data_label, readings[] with timestamp, heart_rate_bpm, spo2_pct, sleep_hours, body_temp_c.

## GET /api/alerts
`contract/examples/alerts.json`
Fields per alert: id, rule, severity ("notice" | "watch" | "attention"), metric, value,
baseline (null when there is not enough history), timestamp, message.
Most severe first. Ids are a1, a2, ... in that order.

## POST /api/assistant/ask
Request: `contract/examples/assistant_ask_request.json` (question 1 to 1000 characters, alert_id optional).
Response: `contract/examples/assistant_ask.json`
Fields: answer, mode ("llm" | "retrieval_only"), citations[] (title, source, url, excerpt), disclaimer.
Always 200 once the alert exists, even when the model is slow or down (mode becomes "retrieval_only").

## Errors
`contract/examples/error.json`
```
{ "error": { "code": "NOT_FOUND" | "VALIDATION_ERROR" | "METHOD_NOT_ALLOWED" | "INTERNAL_ERROR", "message": "..." } }
```
Status codes: 404 unknown alert or route, 422 invalid request, 500 unexpected error.

## Conventions
- All timestamps are UTC ISO 8601 with a trailing Z.
- Every response that carries data includes or implies data_label "SIMULATED".
