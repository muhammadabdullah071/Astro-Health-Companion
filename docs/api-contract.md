# API contract v1 (with Ammara's additions)

Base URL in development: http://localhost:8000. The example files in `contract/examples/`
are the source of truth, and `backend/tests/test_contract.py` fails if a live response
has different fields. Changes need Abdullah and Elthiero to agree and a message in the group chat.

The alert additions below are ADDITIVE: no existing field was renamed or removed, so a frontend
written against the original contract keeps working.

## GET /api/status
`contract/examples/status.json`
Fields: backend ("ok" | "error"), offline_mode, llm ("ready" | "unavailable"),
documents_indexed, last_data_update (newest reading, UTC), data_label.

## GET /api/profile
`contract/examples/profile.json` (proposal: the guide does not define this shape)
Fields: id, name, mission, mission_day, baseline_window_days, data_label.
`id` is the fictional astronaut served (ASTRO-01 by default; set `ASTRO_ID=ASTRO-02` for the second profile).
`mission_day` counts from the first reading (day 1 = 2026-10-16), so it matches Sofia's `mission_day` and
Ammara's day numbers: the HR-01 demo alert is on mission day 20 and the newest reading is day 30.

## GET /api/readings?days=14
`contract/examples/readings.json`
`days` is 1 to 90. Readings are the last N relative to the newest reading, oldest first.
Fields: data_label, readings[] with timestamp, heart_rate_bpm, spo2_pct, sleep_hours, body_temp_c.
`body_temp_c` is WEARABLE SKIN temperature in degrees Celsius. The field name is kept because the
contract is frozen; label the card "Skin temperature" in the UI. Core temperature is a separate,
manual, confirmatory reading and is never part of this field.

## GET /api/alerts?days=14
`contract/examples/alerts.json`
`days` is 1 to 90 (default 14): alerts raised within the last N readings, the same window as
`/api/readings?days=N`, so the chart can draw alert markers. Alerts are evaluated on EVERY day,
not only the latest one. Order: most severe first, then newest first. Ids are a1, a2, ... in that order.

| Field | Meaning |
|-------|---------|
| `id` | Alert id, used as `alert_id` when asking the assistant |
| `rule_id` | HR-01, HR-02, SPO2-01, SLEEP-01, SLEEP-02, TEMP-01, DATA-01 or DATA-02 |
| `rule` | Exact rule name from Ammara's table |
| `severity` | `notice`, `watch` or `attention` (lowercase; show uppercase in the UI) |
| `category` | `physiological`, `data_quality` or `setup` (data_quality and setup use the grey badge) |
| `metric` | Which reading: heart_rate_bpm, spo2_pct, sleep_hours, body_temp_c |
| `value`, `unit` | Measured value and its unit: bpm, %, hours, °C. `value` is null for data-quality alerts |
| `baseline` | The astronaut's own baseline, or null when not established |
| `delta` | value minus baseline (signed), or null |
| `baseline_status` | `established` or `not_established` (baseline is null when not established) |
| `timestamp` | When the triggering reading was taken |
| `message` | Plain-language explanation |
| `next_step` | Suggested next step (Ammara's wording) |
| `source` | "Prototype rule (context: S2, S4)", "Team guide rule (context: S7)" and so on |
| `data_quality` | `good`, `poor` or `insufficient` |
| `data_label` | Always `SIMULATED` |
| `temp_type`, `sensor_location`, `device`, `measurement_method` | Set on TEMP-01 only (`skin`, location, device id, `wearable`); null on every other alert |

The alert card order Ammara asked for (severity tag, rule id and name, metric, value and unit, baseline,
difference, timestamp, data-quality state, explanation, next step, source, disclaimer) maps directly
onto these fields.

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

## Not in contract v1 (needs agreement first)
- Manual core-temperature entry (form and endpoint). Stored separately, never used in the skin baseline,
  never creates an alert or a fever label on its own.

## Conventions
- All timestamps are UTC ISO 8601 with a trailing Z.
- Every response that carries data includes or implies data_label "SIMULATED".
