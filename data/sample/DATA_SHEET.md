# SIMULATED Data Sheet — Astro-Health Companion
 
**Owner:** Sofia  
**Scope:** 30 days × 2 fictional astronaut profiles (60 observations). **All measurements are SIMULATED.** No real astronaut participant data have been accessed or used. Decision support only; not a diagnosis tool.


 **NASA OSDR:** [Repository overview](https://science.nasa.gov/biological-physical/data/osdr/), [Biological Data API](https://visualization.osdr.nasa.gov/biodata/api/). Used only for research context and dataset exploration, **not to fit any values in these generated files**.

## Data dictionary

| CSV field | Unit and meaning | Measurement convention |
|---|---|---|
| `timestamp` | ISO 8601 UTC | One reading at **08:00 UTC** per mission day |
| `heart_rate_bpm` | bpm | Fictional resting spot heart-rate reading |
| `spo2_pct` | % | Fictional spot oxygen-saturation reading; quality stored separately |
| `sleep_hours` | h | Prior overnight sleep ending at 08:00 on the record's date |
| `body_temp_c` | °C | Fictional wearable **skin** temperature at left wrist; the legacy header preserves import compatibility; **not core temperature** |

`traceability.csv` records `profile_id`, `mission_day`, `anomaly_id`, quality states, assumed skin site and sensor, timestamp convention and SIMULATED provenance. Per-profile IDs cannot be reconstructed from a combined five-column CSV without the manifest.

## Parameter ledger: every numerical value

| Parameter | Exact setting | Origin and limitations |
|---|---|---|
| Number of days | 30 each | Team deliverable; chosen demo length |
| Number of profiles | 2 (ASTRO-01, ASTRO-02) | Team deliverable; entirely fictional |
| Start date | 2026-10-16 | Engineering choice matching the starting date|
| End date | 2026-11-14 | Computed from start + 29 days |
| Observation time | 08:00 UTC daily | Ammara's resting-HR protocol; adopted as common demo timestamp |
| Reproducibility seed | 20261113; random stream uses `seed + profile index` | Engineering reproducibility, not a medical parameter |
| Nominal HR | ASTRO-01 = 62 bpm; ASTRO-02 = 65 bpm | Engineering values within Ammara's ordinary 56–68 bpm simulator interval |
| HR variation | Discrete {-2,-1,0,0,0,+1,+2} bpm | Engineering noise approximation; not empirically fitted |
| Nominal SpO2 | ASTRO-01 = 97%; ASTRO-02 = 98% | Engineering values within ordinary 96–99% simulator interval |
| SpO2 variation | {-1,0,0,0,+1} percentage points, clamped to 96–99% | Engineering noise; not validated sensor performance |
| Nominal sleep | ASTRO-01 = 7.0h; ASTRO-02 = 7.2h | Engineering values within Ammara's ordinary 6.5–7.5h simulator interval |
| Sleep variation | {-0.3,-0.2,-0.1,0,+0.1,+0.2,+0.3}h, clamped to 6.5–7.5h, 0.1h precision | Engineering model; one night associated with the following morning's date |
| Nominal wrist skin temperature | ASTRO-01 = **33.2°C**; ASTRO-02 = **33.4°C** | Explicit synthetic engineering assumptions, **not clinically established skin temperatures or NASA measured values** |
| Skin-temperature variation | {-0.2,-0.1,0,0,+0.1,+0.2}°C, 0.1°C precision | Engineering model; no device validation or diurnal profile |
| Temperature site/window | left wrist; 08:00 UTC morning | Fictional sensor location and consistent sampling window |
| Skin-temperature data-quality plausibility screen | 28–38°C | Proposed physical-screen interval in Ammara's note, **not a healthy/reference range** |
| Rolling baseline | Previous 7 valid comparable days/nights | Ammara's prototype calibration and baseline specification; the current observation is excluded |
| Days 1–7 | No planted anomalies | Calibration window |
| HR reference before day 20 | Days 13–19 = [60,61,62,63,64,62,62] bpm | Explicitly engineered to average exactly 62 bpm |
| Day 20 HR | 78 bpm; +16 bpm over baseline 62 bpm | Ammara's specified HR-01 demonstration; threshold ≥15 bpm |
| Day 22 SpO2 | 93%, quality=`poor` | Ammara's isolated sensor-data-quality example; **not SPO2-01** |
| SpO2 preceding stable values | Days 15–21 = 97% | Engineered reference preceding isolated day-22 dip |
| Sleep reference preceding day 24 | Days 17–23 = [6.9,7.1,7.0,6.8,7.2,7.1,6.9] hours | Engineered to average 7.0 hours |
| Sleep on days 24–26 | 5.4h, 5.6h, 5.2h |  under six for three consecutive nights yields SLEEP-01 on day 26 |
| HR-02, SPO2-01, TEMP-01 injection | No deliberate triggers | The dataset exercises selected high-value demo cases rather than every rule |
| Core temperature | Not generated | Ammara requires separate manually entered core readings; never mix with skin |

## Rule expectations under the documented rolling-baseline convention

- **HR-01:** day 20, ASTRO-01, **WATCH** (78 − 62 = +16 bpm).
- **HR-02:** not triggered by day 20 alone; its condition needs two consecutive daily HR deviations.
- **SPO2-01:** the 93% observation on day 22 is a **single poor-quality** reading; it must not independently produce a physiological alert.
- **DATA-01:** a data-quality notice can be tested on day 22 if the backend uses the sidecar's `spo2_quality=poor` field. The import CSV alone cannot express quality.
- **SLEEP-01:** day 26, ASTRO-01, **NOTICE**, following 5.4h, 5.6h, and 5.2h on days 24–26.
- **SLEEP-02:** not met by three consecutive nights each ≥1.5h below its *own preceding rolling 7-night* baseline, even though all three nights are under 6h. A multi-night fixed-baseline comparison is a different algorithm and must not be assumed.
- **DATA-02:** initial calibration state applies before seven valid prior observations are available.
- **TEMP-01:** not a deliberately planted scenario. Ammara describes a configurable +0.5°C example with sensor-related quality checks; this file set does not validate sensor accuracy or trigger it on purpose.

## Limitations and interpretation

The profiles are fictional; the values are not distributions fitted to human spaceflight data. Day-to-day variations are simplified, and most metrics do not model real cross-variable dependence, device artifacts, circadian physiology, environment or clinical uncertainty. Skin temperature is especially affected by sensor location and context; its synthetic values cannot be used to infer fever or core temperature. Synthetic events and prototype workflow rules cannot establish alert accuracy, sensitivity, specificity, clinical safety, health status or disease diagnosis. OSDR metadata does not transform these synthesized values into real NASA observations.
All exports are **SIMULATED**.
