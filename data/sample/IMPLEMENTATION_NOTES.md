# Engineering decisions, changes, and modification map

**Final handoff — Sofia, 13 November 2026.** This document explains the selected implementation and how to adapt it. It is not a request for another decision round.

## Changes since the initial team mock data

1. **Two complete 30-day datasets:** The original single CSV example was shorter. We provide `readings.csv` (ASTRO-01) and `readings_profile_02.csv` (ASTRO-02), each with exactly 30 08:00 UTC observations. Files remain separate because the agreed import schema has no `profile_id` column.
2. **Exact import compatibility:** CSV columns stay `timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c` in precisely this order. JSON and internal metadata are companion artifacts rather than breaking schema changes.
3. **Temperature semantics corrected:** Ammara distinguishes wearable **skin temperature** from manual **core temperature**. `body_temp_c` is the existing import name, but the generated value represents simulated **left-wrist skin temperature**. No core-temperature measurement is synthesized, and skin values cannot be interpreted as fever/core measurements.
4. **Calibration protected:** The first seven days have no planted anomalies. The baseline is constructed from seven *preceding* valid readings. An alerting reading must not contaminate its own comparison baseline.
5. **Demo aligned with Ammara's exact examples:** day 20 HR 78 vs 62; day 22 isolated 93% SpO2 with poor signal quality; days 24–26 sleep 5.4, 5.6, 5.2 hours. The isolated SpO2 event is a quality illustration, not a physiological diagnosis or SPO2-01 rule firing.
6. **Data quality separated:** Quality annotations and scenario identifiers live in `traceability.csv`; the five-column CSV is untouched. The backend can import quality metadata separately when it supports DATA-01.
7. **Conditional fixture removed:** Under the implemented previous-seven-night rolling baseline convention, SLEEP-02 is not triggered by three consecutive qualifying nights, whereas SLEEP-01 is triggered on day 26. The fixture describes these as definite scenario expectations, not an unresolved choice.
8. **Clean code and manifest:** Removed internal review-status language from generator comments, execution output and manifest. Scientific limitations remain documented in `DATA_SHEET.md` instead of being written as action items in executable code.

## Exact location of adjustable settings

| Want to change | Edit in `generate_simulated_readings.py` | Then verify |
|---|---|---|
| Number of days, start date, random seed | CLI `--days`, `--start-date`, `--seed`; defaults `DAYS`, `START_DATE`, `SEED` | At least 26 days for built-in scenarios; update dates cited in docs if default changes |
| One or two fictional profiles | CLI `--profiles`; `PROFILE_SETTINGS` | Associate each exported file with the correct profile in SQLite |
| Normal-day HR, SpO2 and sleep baselines | `PROFILE_SETTINGS` | Values still respect the documented ordinary-day ranges |
| Normal-day variability | `make_profile()` noise choices and clamps | Re-run `test_generator.py`; avoid accidentally producing extra alert cases |
| Simulated skin-temperature levels | `SKIN_TEMPERATURE_BASELINES` and `make_profile()` skin noise | Update provenance in `DATA_SHEET.md`; do not treat these as core-temperature values |
| Sensor site, device, time window | Traceability fields in `make_profile()` | Ensure comparisons use matching sites/windows |
| Day-20 HR scenario | `hr_reference` and `if day == 20` | Exactly 78 bpm, previous-seven-day HR mean 62 bpm; update fixture if intentionally changed |
| Day-22 single SpO2 dip | `if day == 22` and `spo2_quality` | One anomalous poor-quality reading; no SPO2-01 on its own |
| Days 24–26 sleep scenario | `sleep_reference`, `if day in (24, 25, 26)` | SLEEP-01 at day 26; update fixture for changed timing or values |
| Five-column import schema | `HEADERS` | **Coordinate changes with the API/seed-script owner first**; otherwise keep frozen |
| Internal provenance columns | `TRACE_HEADERS` and traceability append block | Changes do not affect the agreed readings CSV |
| Expected event examples | `expected_alerts.json` writer in `main()` | Regenerate files and run tests |
| Additional temperature or sensor demo | Add a new event in `make_profile()` and a corresponding fixture | Keep manual core-temperature observations in a separate dataset/table |

## Baseline conventions for downstream code

- **Heart rate, SpO2, skin temperature:** compare a current valid observation against up to seven preceding valid *comparable* records. Exclude invalid readings and do not mix skin sensor sites or sampling windows.
- **Sleep:** compare the current night's duration against the preceding seven valid nights. For the multi-night SLEEP-02 condition, check each night against its own preceding rolling baseline. This is why three nights below six hours can trigger SLEEP-01 without automatically triggering SLEEP-02.
- **Insufficient baseline:** prior to seven usable observations, display `Baseline not established` instead of a personalized physiological deviation alert.
- **Alert persistence:** preserve an alert event's recorded baseline and value when newly arrived observations move the rolling baseline; do not silently rewrite historical alerts.
- **Quality:** invalid SpO2 readings must be excluded from physiological thresholds. The quality sidecar makes this explicit; the five-column CSV alone does not carry that information.

## Handoff owners and file routing

**Elthiero:** `readings.csv` first; `readings_profile_02.csv` separately; `manifest.json` for profile assignment. `traceability.csv` supplies quality flags if data-quality rule demonstrations are enabled.  
**Shubhi:** `expected_alerts.json` plus `test_generator.py` for seeded scenario checks.  
**Abdullah:** API-shaped JSON examples, visible SIMULATED badge, and **Skin temperature** UI label for the `body_temp_c` value.  
**Ammara:** `DATA_SHEET.md` documents provenance and the limits of the engineering assumptions; none of the synthetic readings are astronaut norms.

## Scope boundary

No real astronaut health records are included. No clinically validated thresholds, medical diagnoses, core temperature estimates, CV fatigue detection, or SANS prediction model are claimed. The source-aligned workflow is **SIMULATED telemetry → transparent prototype alerts → offline cited decision support**.
