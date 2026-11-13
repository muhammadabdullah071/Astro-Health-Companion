# Placeholders and assumptions

Everything below works today with a reasonable default. Replace it when the owner delivers.
Nothing here should reach the final demo unreviewed.

| Item | Placeholder used now | Owner | Where to change |
|------|----------------------|-------|-----------------|
| Indicator list | heart rate, SpO2, sleep hours, body temperature | Ammara, Sofia | schema.sql, seed.py, rules.py |
| Alert thresholds | HR +15 bpm over baseline (watch), HR above 100 (attention), SpO2 below 94 (watch) and 90 (attention), temperature 37.8 C (watch) and 38.0 C (attention), sleep under 6 h for 3 nights (notice) | Ammara | backend/app/engine/rules_config.py only |
| Severity names | notice, watch, attention | Ammara, Abdullah | rules_config.py (SEVERITY_RANK) |
| Alert wording and next steps | generic safe wording | Ammara (review) | rules_config.py and rules.py messages |
| Rule sources | "PLACEHOLDER: source to be added by Ammara" | Ammara | rules_config.py (source) |
| Baseline method | mean of previous 7 days, current day excluded; skipped when fewer than 3 days | Ammara | rules_config.py |
| Sample data | generated, seed 42, 30 days ending 2026-11-14T08:00:00Z, planted demo anomalies | Sofia | data/sample/readings.csv (same columns) |
| Mission start date | 2026-06-25 (gives mission day 143 on 14 Nov) | team | backend/app/db/seed.py (PROFILE) |
| Astronaut profile | "Demo Astronaut A" | team | backend/app/db/seed.py (PROFILE) |
| Profile response fields | id, name, mission, mission_day, baseline_window_days, data_label (the guide gives no shape) | Abdullah and Elthiero agree | routes/profile.py and contract/examples/profile.json |
| Assistant | placeholder answer and placeholder citations | Cesar | create rag/ask.py (see below) |
| Documents indexed | 0 until rag/index/meta.json exists | Cesar | rag/index/meta.json |
| Ollama address | http://127.0.0.1:11434 | Cesar | OLLAMA_URL environment variable |
| Model timeout | 20 seconds, then retrieval-only | Elthiero, Cesar | ASK_TIMEOUT_SECONDS |
| Offline flag | true | Elthiero | OFFLINE_MODE |
| Frontend ports allowed by CORS | 3000 and 3001 (localhost and 127.0.0.1) | Abdullah | CORS_ORIGINS |

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

- `alert` is a dict with: id, rule_id, rule, severity, metric, value, baseline, timestamp,
  message, next_step, source. It is None when the user asks without choosing an alert.
- `retrieval_only` must NOT call the language model.
- If evidence is missing, return the answer "I cannot answer that from my sources." with no citations.
- After indexing, write `rag/index/meta.json` containing `{"documents_indexed": 12}`.
- Do not add the disclaimer. The backend adds it.

The backend loads this module automatically. If it is missing or fails to import, the
placeholder stub is used and the API keeps working.
