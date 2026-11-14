# Astro-Health Companion — Final simulated-data handoff

**Owner:** Sofia  
**Handoff date:** 13 November 2026  
**Data classification:** **SIMULATED** — fictional demonstration readings, not NASA astronaut observations.  
**Intended use:** Offline dashboard, SQLite seed import, baseline/alert demonstrations, and deterministic QA. Not a medical diagnosis tool.

## Import first

 **`readings.csv`** for `ASTRO-01`. It contains 30 daily rows and the **exact five headers** requested:

```csv
timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c
```

Import `readings_profile_02.csv` separately for `ASTRO-02`, mapping each file to the corresponding fictional profile using `manifest.json`. Do not concatenate the CSV files without adding the profile identity in the database: both profiles use the same daily timestamps. JSON equivalents are included for convenience.

**Column semantics:** `body_temp_c` contains **simulated wearable skin temperature**, not core temperature. This column name is retained to match the agreed import schema. The UI label is **Skin temperature**. No core-temperature observations are generated; any manual core-temperature feature must store its observations separately. This mapping is a documented integration decision, not a claim of sensor calibration.

**Sleep convention:** A reading timestamp of `08:00:00Z` on day N records the previous overnight sleep period ending that morning. This is the convention implemented throughout the dataset.

## Reproduce files

Python 3.9+; only the standard library is required.

```bash
python generate_simulated_readings.py --profiles 2 --days 30 --out .
python -m unittest discover -s . -p 'test_*.py' -v
```

The generator uses a fixed random seed and internally checks the schema, timestamps, day-1–7 calibration period, day-20 heart-rate event, day-22 isolated low-quality SpO2 observation, and days-24–26 sleep event. It re-creates the CSVs, JSONs, traceability, manifest and expected-alert scenarios.

## Included files

| File | Purpose |
|---|---|
| `readings.csv` | **Primary SQLite import** — ASTRO-01, 30 rows, agreed 5-column schema |
| `readings_profile_02.csv` | ASTRO-02, 30 rows, same schema |
| `readings.json`, `readings_profile_02.json` | API-shaped equivalents with `data_label: SIMULATED` |
| `traceability.csv` | Sidecar with profile, mission day, anomaly labels, sensor quality and measurement semantics; **not part of the 5-column import** |
| `expected_alerts.json` | Reproducible scenario expectations and required quality-sidecar condition for DATA-01 |
| `manifest.json` | Dataset ownership, date range, seed and measurement semantics |
| `generate_simulated_readings.py` | Standard-library generator and validation |
| `test_generator.py` | Handoff regression tests |
| `DATA_SHEET.md` | Sources, parameter origins, limitations, exact demo numbers |
| `IMPLEMENTATION_NOTES.md` | What changed, why, and where to edit for other scenarios |

## Demo events

- **Days 1–7:** clean calibration observations; personalised deviation alerts start only after a usable baseline is established.
- **Day 20:** 78 bpm versus the seven preceding HR readings averaging exactly 62 bpm → **HR-01 WATCH**. This single-day event is **not HR-02**.
- **Day 22:** isolated SpO2 reading of 93% with `spo2_quality=poor` in `traceability.csv`. No physiological SpO2 alert is supported. To show a **DATA-01** quality notice, import or otherwise consume the sidecar quality flag.
- **Days 24–26:** 5.4, 5.6 and 5.2 sleep hours → **SLEEP-01 NOTICE** at day 26. Under the preceding-seven-night rolling baseline convention, this sequence **does not** meet the three-consecutive-night condition for SLEEP-02.

The demo does not inject TEMP-01, HR-02 or SPO2-01 physiological alerts. 
## Integration notes

The five-column CSV cannot encode sensor quality, profile identity, or anomaly annotations. These are provided in `traceability.csv`. `data_label=SIMULATED` is included in JSON payloads and the manifest; the frontend should retain its persistent **SIMULATED DATA** label.

NASA OSDR provides scientific context, **not** the actual numbers in these synthetic datasets.
