# Placeholders and assumptions

Rules, names, severities, next steps and sources now come from Ammara's deliverables pack (13 Nov 2026).
What is still a placeholder or an assumption is listed here. Nothing here should reach the final demo unreviewed.

## Implemented from Ammara's pack

| Rule | Trigger as implemented | Severity | Category |
|------|------------------------|----------|----------|
| HR-01 | latest valid resting heart rate is 15 bpm or more above the baseline | watch | physiological |
| HR-02 | HR-01 condition on 2 consecutive daily readings | attention | physiological |
| SPO2-01 | 3 or more percentage points below baseline on 2 consecutive valid readings | watch | physiological |
| SLEEP-01 | sleep under 6 hours on 3 consecutive nights (needs no baseline) | notice | physiological |
| SLEEP-02 | sleep 1.5 hours or more below baseline on 3 consecutive nights | watch | physiological |
| TEMP-01 | skin temperature 0.5 C or more above the skin baseline on 2 consecutive comparable readings, per time window | watch | physiological |
| DATA-01 | missing, poor quality or gapped readings | notice | data_quality |
| DATA-02 | fewer than 7 usable comparable readings and no preflight baseline | notice | setup |

Removed from the old engine because they are population cut-offs: absolute SpO2 limits (94 and 90),
absolute temperature limits (37.8 and 38.0 C) and the absolute heart rate limit (100 bpm).

## Assumptions to confirm with Ammara (send her this list)

1. **Baseline window with exclusions.** The baseline is the last 7 valid, non-flagged, comparable readings
   found within the previous 14 readings (`BASELINE_LOOKBACK_ROWS`). A fixed 7 day window would drop below 7
   readings after every alert and raise DATA-02 by mistake.
2. **What "flagged" means** (a reading that is excluded from later baselines): HR 15 bpm or more above baseline;
   SpO2 3 points or more below; sleep under 6 hours OR 1.5 hours or more below baseline; skin temperature at or
   above `temp_delta_threshold`.
3. **"Consecutive".** HR-02 and SLEEP-01 and SLEEP-02 use adjacent daily rows. SPO2-01 uses the previous VALID
   reading. TEMP-01 uses the previous COMPARABLE reading (same time window and sensor location) at least
   `min_gap_hours` (4) earlier.
4. **Stale or missing data (DATA-01).** Detected as a gap longer than 36 hours between readings, not against the
   wall clock, so the offline demo never fires it by accident.
5. **DATA-02 history.** It is raised on each calibration day (days 1 to 7). The default 14 day window hides them
   in the demo; `/api/alerts?days=26` shows them.
6. **Alert history.** Alerts are evaluated on every day. `/api/alerts` returns the last N days (default 14).
   The dataset must end near day 26 so both demo anomalies fall inside that window.
7. **Skin temperature.** Stored in `body_temp_c` (frozen contract name). Time windows are overnight 0 to 6,
   morning 6 to 12, afternoon 12 to 18, evening 18 to 24 (UTC hour).
8. **Sensor accuracy and noise** (0.2 and 0.1 C) are placeholders; the app refuses to start if
   `temp_delta_threshold` is lower than their sum.

## Other placeholders

| Item | Placeholder used now | Owner | Where to change |
|------|----------------------|-------|-----------------|
| Sample data | generated, seed 42, 26 days ending 2026-11-14T08:00:00Z; day 20 HR 78, days 24 to 26 sleep under 6 h | Sofia | data/sample/readings.csv (same columns) |
| Skin temperature range | 33.3 to 33.7 C | Sofia | data/generate_placeholder_data.py |
| Quality columns | defaults: good, wearable, wrist, wearable-01, contact good, no dropout | Sofia | CSV columns (optional) |
| Preflight baseline | none | Ammara | `PREFLIGHT_BASELINE` in rules_config.py |
| Mission start date | 2026-06-25 (mission day 143 on 14 Nov) | team | backend/app/db/seed.py (PROFILE) |
| Profile response fields | id, name, mission, mission_day, baseline_window_days, data_label | Abdullah and Elthiero | routes/profile.py and contract/examples/profile.json |
| Assistant | placeholder answer and placeholder citations | Cesar | create rag/ask.py (see below) |
| Documents indexed | 0 until rag/index/meta.json exists (Ammara's library has 9 sources) | Cesar | rag/index/meta.json |
| Ollama address | http://127.0.0.1:11434 | Cesar | OLLAMA_URL |
| Model timeout | 20 seconds, then retrieval-only | Elthiero, Cesar | ASK_TIMEOUT_SECONDS |
| Offline flag | true | Elthiero | OFFLINE_MODE |
| CORS ports | 3000 and 3001 | Abdullah | CORS_ORIGINS |

## Interface to agree with Cesar (send him this)

Create `rag/ask.py` with two functions:

```python
def ask(question: str, alert: dict | None) -> dict: ...
def retrieval_only(question: str, alert: dict | None) -> dict: ...
```

Both return:

```python
{"answer": str,
 "mode": "llm" | "retrieval_only",
 "citations": [{"title": str, "source": str, "url": str, "excerpt": str}]}
```

- `alert` is a dict with: id, rule_id (HR-01 ...), rule, severity, category, metric, value, unit, baseline, delta,
  baseline_status, timestamp, message, next_step, source, data_quality, temp_type, sensor_location, device,
  measurement_method. It is None when the user asks without choosing an alert.
- Use `rule_id` and `next_step` when explaining an alert, and match the wording in `message`.
- Never infer a diagnosis, fever or immune condition from the indicators or from skin temperature.
- `retrieval_only` must NOT call the language model.
- If evidence is missing, return "I cannot answer that from my sources." with no citations.
- After indexing, write `rag/index/meta.json` containing `{"documents_indexed": 9}`.
- Do not add the disclaimer. The backend adds it.

The backend loads this module automatically. If it is missing or fails to import, the
placeholder stub is used and the API keeps working.
