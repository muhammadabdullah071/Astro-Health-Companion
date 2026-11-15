# Scientific Library, Indicators and Evidence Provenance

**Astro-Health Companion** | NASA International Space Apps Challenge 2026 | Challenge: Health Monitoring Software

> **All data in this project is SIMULATED.** Decision support only - not a medical diagnosis.

| | |
|---|---|
| **Owner** | Ammara (Medical Research, Health Indicators, UX) |
| **Folder** | `library/` |
| **Last updated** | 15 November 2026 |
| **Status** | Prepared, with open items listed in [Section 13](#13-open-items-and-status) |

---

## Contents

1. [Purpose of this folder](#1-purpose-of-this-folder)
2. [Scope and scientific framing](#2-scope-and-scientific-framing)
3. [Indicator specification](#3-indicator-specification)
4. [Temperature monitoring strategy](#4-temperature-monitoring-strategy)
5. [Alert rules](#5-alert-rules)
6. [Alert card format](#6-alert-card-format)
7. [Evidence map (provenance)](#7-evidence-map-provenance)
8. [Curated scientific library (9 sources)](#8-curated-scientific-library-9-sources)
9. [Source evaluation](#9-source-evaluation)
10. [Domain assumptions register](#10-domain-assumptions-register)
11. [Design and labelling rules](#11-design-and-labelling-rules)
12. [Limitations and ethics](#12-limitations-and-ethics)
13. [Open items and status](#13-open-items-and-status)
14. [Review log](#14-review-log)
15. [How each teammate uses this folder](#15-how-each-teammate-uses-this-folder)
16. [Glossary](#16-glossary)
17. [Files, licensing and credits](#17-files-licensing-and-credits)

---

## 1. Purpose of this folder

This folder holds the medical-research side of the project: which health indicators we monitor, how each is compared with the astronaut's own baseline, which transparent rules raise alerts, and which scientific sources support the context behind them.

It answers three questions a judge may ask:

- **What did you measure, and why?** Sections 2-4.
- **Where does each rule come from?** Sections 5 and 7.
- **How honest are you about what the evidence supports?** Sections 9, 10 and 12.

The central message is that **every numeric trigger is a prototype workflow rule, not a medical threshold.** None of the nine curated sources establishes a numeric threshold, and the app never labels a value normal or abnormal against a population cut-off. It only reports deviation from each person's own baseline.

---

## 2. Scope and scientific framing

The MVP monitors four indicators: **resting heart rate, oxygen saturation (SpO2), sleep duration and body temperature.** Each is compared with the astronaut's own baseline, shown as a 14-day trend, and checked by plain-English rules.

The four scientific domains behind the project are framing only and are **not** turned into diagnostic scores:

| Domain | Where it appears in the project |
|---|---|
| Immune | Temperature context (S6); wearables cannot diagnose immune dysfunction |
| Bone and muscle | Exercise-countermeasure context (S9); exercise logs do not measure bone density or muscle mass |
| Cardiovascular | Heart rate and SpO2 context (S2, S3, S4) |
| Behavioural health | Sleep context (S7); sleep alone does not diagnose a behavioural-health condition |

**Optional context inputs (future work, not in the MVP):** exercise logs, fatigue, mood, symptoms, blood pressure, and radiation, CO2 or noise data.

**Evidence boundary.** The curated sources do not establish universal astronaut normal ranges or clinically validated thresholds. For that reason the app reports deviation from each person's own baseline, and all numeric triggers in this document are prototype workflow rules.

---

## 3. Indicator specification

| Indicator | Unit | Measurement and quality | Baseline method | Simulation range | Clinical boundary |
|---|---|---|---|---|---|
| Resting heart rate | bpm | One reading per day at 08:00 under resting conditions; the 08:00 reading is defined as resting by protocol | 7-day rolling mean of valid readings, excluding readings that triggered an alert | 56-68 | No inference of arrhythmia, cardiovascular disease or immune dysfunction; repeat unusual readings |
| Oxygen saturation (SpO2) | % | Spot reading with signal-quality check; record timestamp and device | 7-day mean of valid readings; poor-quality readings stored separately | 96-99 | Not a diagnosis of hypoxia or cardiopulmonary disease; a poor-quality reading is a data problem, not an alert |
| Sleep duration | hours per night | Nightly total; record source (wearable or manual) | 7-night rolling mean; compare current night and multi-night pattern | 6.5-7.5 on normal nights | Sleep alone does not diagnose a behavioural-health or psychiatric condition |
| Skin temperature (wearable, **primary**) | °C | Timestamp, sensor location and device recorded with every reading; contact quality and conditions checked | 7-day rolling mean of valid, comparable skin-temperature readings only, per time window | To be set by Sofia (separate from core) | Not a core-temperature measurement; no inference of fever, infection or immune dysfunction |
| Core temperature (manual, **secondary**) | °C | Manual entry: value, unit, timestamp, site, method, device; taken per approved protocol | None. Stored separately; never used in the wearable baseline | Core reference values defined separately | Confirmatory only; not a continuous indicator |

> Simulation ranges exist only so the data generator produces plausible values. **They are not clinical normal ranges.**

### Baseline policy

- Days 1-7 form a **calibration window**, or a comparable preflight baseline is used if one is supplied.
- Until a usable baseline exists, the app shows **"Baseline not established"** and raises no personalised deviation alerts (rule DATA-02).
- Rolling baselines are recalculated openly.
- An active alert is never silently normalised.
- Raw readings and timestamps are always retained.

---

## 4. Temperature monitoring strategy

Skin temperature and core temperature are **different physiological measurements and are not interchangeable.** The app keeps them apart at every level: storage, baseline, alerts and display.

### Primary: skin temperature (wearable)

- Monitored through a wearable sensor and recorded in °C with timestamp, sensor location and device information.
- A 7-day rolling baseline is built from valid and comparable skin-temperature readings only.
- New readings are compared with the individual's personal skin baseline to identify sustained deviations.
- Sensor placement, contact quality and environmental conditions are considered when interpreting changes.
- Skin readings are never interpreted as direct measurements of core body temperature.

### Secondary: core temperature (manual entry)

- A separate, confirmatory measurement, not a continuous wearable indicator.
- If a temperature alert or other concern needs further assessment, a core reading may be taken under the approved medical or mission protocol and entered manually (value, unit, timestamp, site, method, device).
- Stored separately and **never combined** with skin readings when calculating the baseline.
- Displayed beside the skin trend, labelled **"Manual core reading (confirmatory)"**.
- It does not change the skin baseline and does not generate a diagnosis, fever label or new alert on its own. Interpretation follows the approved medical or mission protocol, not the app.

### Additional design rules (proposed values, pending confirmation by Sofia and Elthiero)

| Rule | Detail |
|---|---|
| Configurable threshold | The +0.5 °C trigger is a provisional placeholder. It is stored as `temp_delta_threshold`, not hard-coded, and is set no lower than the sensor's combined accuracy and noise margin. |
| Circadian rhythm | Readings are compared with the baseline for the **same time window** (for example overnight or morning), not an all-day average. If a window has too few comparable readings, the app shows "Baseline not established" for that window. |
| Sustained deviation | Counts only when the threshold is exceeded on at least two readings in the same window, separated by at least 4 hours (proposed), or on two consecutive days. A single spike never triggers TEMP-01. |
| Valid reading | All of: (a) timestamp, sensor location and device ID present; (b) good contact quality; (c) within a plausible physical range of 28-38 °C (proposed); (d) no sensor dropout in the preceding period; (e) same sensor location as the baseline readings. Invalid readings are stored but excluded from the baseline and alerts, and feed DATA-01. |

**Scientific boundary.** Wearable skin-temperature changes may provide useful monitoring information but cannot independently establish elevated core temperature or diagnose a medical condition.

---

## 5. Alert rules

Severity levels follow the Team Execution Guide: **NOTICE, WATCH, ATTENTION.** They are operational alert levels, not clinical acuity labels. Rule names below are the exact strings the API returns.

| ID | Rule name | Trigger logic | Severity | Suggested next step |
|---|---|---|---|---|
| HR-01 | Resting heart rate above personal baseline | Latest valid resting heart rate is 15 bpm or more above the 7-day baseline | WATCH | Repeat at rest under the same conditions; review recent sleep, exercise and symptoms; follow the mission-approved protocol if it persists or symptoms appear |
| HR-02 | Persistent heart rate deviation | The HR-01 condition holds on 2 consecutive daily readings | ATTENTION | Repeat the measurement; review trend and symptoms; contact ground or medical officer per mission protocol |
| SPO2-01 | SpO2 below personal baseline | Valid readings 3 or more percentage points below baseline on 2 consecutive valid readings | WATCH | Repeat with good signal quality; check device fit and conditions; review symptoms and protocol |
| SLEEP-01 | Sleep under 6 hours for 3 nights | Sleep is under 6 hours on 3 consecutive nights | NOTICE | Review schedule, workload, environment and fatigue; consider approved sleep countermeasures |
| SLEEP-02 | Sleep below personal baseline | Nightly sleep is 1.5 hours or more below baseline on 3 consecutive nights | WATCH | Fatigue and mood check-in if available; schedule and rest review; monitor the trend |
| TEMP-01 | Skin temperature above personal baseline | Comparable valid skin-temperature readings are 0.5 °C or more above the skin baseline on 2 consecutive readings, compared per time window; threshold is configurable and pending review against sensor accuracy | WATCH | Repeat with the same site and method; check contact quality and conditions; if it persists or symptoms appear, a manual core-temperature measurement may be taken and entered per medical protocol |
| DATA-01 | Insufficient or unreliable data | Missing, stale, badly formatted or poor-quality readings prevent a valid comparison | NOTICE (data quality) | Show "insufficient data"; request a repeat or manual entry; infer no health event |
| DATA-02 | Baseline not established | Fewer than 7 days of usable comparable data and no approved preflight baseline | NOTICE (setup) | Keep collecting; show raw trends without personalised alerts |

DATA-01 and DATA-02 are **not physiological alerts.** They are kept separate in the API (`category`: `physiological`, `data_quality` or `setup`).

**Demo scenario.** Day 20: heart rate 78 bpm against a 62 bpm baseline (+16 bpm) fires HR-01. Days 24-26: sleep under 6 hours fires SLEEP-01. Days 1-7 stay clean. All demo data stays inside the labelled SIMULATED dataset.

---

## 6. Alert card format

Every alert card shows, in this order:

1. Severity tag
2. Rule ID and name
3. Metric
4. Measured value and unit
5. Personal baseline
6. Difference
7. Timestamp
8. Data-quality state
9. Plain-language explanation
10. Suggested next step
11. Source, or "prototype rule"
12. Disclaimer

**Example wording:** *WATCH - Resting heart rate is 78 bpm, 16 bpm above this astronaut's 7-day baseline of 62 bpm. Rule HR-01 fired. Recheck at rest and review the trend. This is a monitoring alert, not a diagnosis.*

The SIMULATED badge and the line **"Decision support only - not a medical diagnosis"** stay visible on every screen and in exported data.

---

## 7. Evidence map (provenance)

This table shows where each rule comes from and, just as importantly, what its context sources do **not** prove.

| Rule | Numeric trigger | Origin | Context sources | What the sources do not prove |
|---|---|---|---|---|
| HR-01 | +15 bpm vs 7-day baseline | Prototype rule | S2, S4 | S2 mixes astronaut, analog and animal evidence and discusses heart-rate variability, not this bpm trigger. S4 has open questions on sensor accuracy and is abstract-only. Neither validates a 15 bpm cut-off. |
| HR-02 | HR-01 on 2 consecutive days | Prototype rule | S3, S5 | S3 and S5 support onboard decision support and Earth-independent operations in general. They do not prove this prototype is clinically effective or safe. |
| SPO2-01 | -3 points on 2 valid readings | Prototype rule | S4 | S4 does not validate wearable SpO2 accuracy in flight or this 3-point delta. |
| SLEEP-01 | Under 6 h for 3 nights | Team Execution Guide rule | S7 | S7 is a framework, not a validated predictive model. It does not establish a 6 h cut-off. |
| SLEEP-02 | -1.5 h vs baseline for 3 nights | Prototype rule | S7 | As above. Sleep alone does not diagnose a behavioural-health condition. |
| TEMP-01 | +0.5 °C skin vs baseline (configurable) | Prototype rule | S4, S6 | S6 states that immune outcomes need laboratory tests. Wearable skin temperature cannot establish fever, infection or immune dysfunction. The threshold awaits review against sensor accuracy. |
| DATA-01 | Invalid or missing reading | Data-quality rule | None (not physiological) | Not applicable. It infers no health event. |
| DATA-02 | Under 7 days of usable data | Setup rule | None (not physiological) | Not applicable. It exists to prevent false precision. |

Reference-only sources with no direct rule: **S1** (broad hazard context), **S8** (radiation context), **S9** (musculoskeletal context).

---

## 8. Curated scientific library (9 sources)

The library meets the Team Execution Guide's 8-15 target. Each entry was checked against its publisher, PubMed or PMC record. **DOI is the stable link.** The machine-readable version is `sources.csv` (see Section 17).

| ID | Citation | Identifier |
|---|---|---|
| S1 | Winkler LH. Human physiological limitations to long-term spaceflight and living in space. *Aerosp Med Hum Perform.* 2023;94(6):444-456. | doi:10.3357/AMHP.6190.2023; PMID 37194175 |
| S2 | Tomsia M, Cieśla J, Śmieszek J, et al. Long-term space missions' effects on the human organism: what we do know and what requires further research. *Front Physiol.* 2024;15:1284644. | doi:10.3389/fphys.2024.1284644 |
| S3 | Russell BK, Burian BK, Hilmers DC, et al. The value of a spaceflight clinical decision support system for Earth-independent medical operations. *npj Microgravity.* 2023;9:46. | doi:10.1038/s41526-023-00284-1; PMC10284846 |
| S4 | Gupta R, Ghosh PS. Advancements in health monitoring technologies for astronauts in deep space missions: a review. *Life Sci Space Res.* 2025;47:190-196. | doi:10.1016/j.lssr.2025.06.011; PMID 41136019 |
| S5 | Levin DR, Steller J, Anderson A, et al. Enabling human space exploration missions through progressively Earth independent medical operations (EIMO). *IEEE Open J Eng Med Biol.* 2023;4:162-167. | doi:10.1109/OJEMB.2023.3255513; PMC10810302 |
| S6 | Marchal S, Choukér A, Bereiter-Hahn J, et al. Challenges for the human immune system after leaving Earth. *npj Microgravity.* 2024;10 (published 18 Nov 2024). | doi:10.1038/s41526-024-00446-9 |
| S7 | Barbour BN, Twardowska K, Favero N, et al. Biopsychosocial health considerations for astronauts in long-duration spaceflight: a narrative review. *Wilderness Environ Med.* 2025;36(1_suppl):123S-137S. | doi:10.1177/10806032241289106; PMID 39470395 |
| S8 | Narici L, Baiocco G, Cenci G, et al. Radiation risk mitigation in human space exploration: a primer, a vision, and the state of the art. *Eur Phys J Plus.* 2026;141:100. | doi:10.1140/epjp/s13360-025-07199-8 |
| S9 | Roberts BM, Deane CS, Szewczyk NJ, et al. Musculoskeletal responses to spaceflight: mechanisms, countermeasures, and key gaps. *Am J Physiol Cell Physiol.* 2025;329(6):C1985-C1993. | doi:10.1152/ajpcell.00649.2025 |

---

## 9. Source evaluation

| ID | Type | What it supports | Key limitation | Access and licensing |
|---|---|---|---|---|
| S1 | Narrative review (single author) | Broad multi-system hazard context | Routine wearables cannot detect every change | To confirm |
| S2 | Review | Multi-system effects; heart-rate variability as an adaptation marker | Mixes astronaut, analog and animal evidence | To confirm |
| S3 | Research article | Case for onboard clinical decision support | Does not prove this prototype is clinically effective or safe | PMC record exists; licence to confirm |
| S4 | Review | Wearables, miniaturisation, AI-assisted interpretation | Sensor accuracy and flight validation remain open | **Abstract-level access only.** Full text to be confirmed by Cesar |
| S5 | Framework paper | Earth-independent medical operations framework | Not a trial of a monitoring app | PMC record exists; licence to confirm |
| S6 | Review | Spaceflight stressors and immune regulation | Immune outcomes need laboratory tests; wearables cannot diagnose immune dysfunction | To confirm |
| S7 | Narrative review | Isolation, sleep, stress, mood and team factors | A framework, not a validated predictive model | **Full-text access to be confirmed by Cesar** |
| S8 | Review (primer) | Radiation context only | Exposure and biological risk are different; wearables do not diagnose radiation injury | To confirm |
| S9 | Review | Bone, muscle and tendon context; exercise countermeasures | Exercise logs do not measure bone density or muscle mass | To confirm |

**Key point for judges:** none of the nine sources establishes a specific numeric threshold. That is why every numeric rule is labelled a prototype rule, and why the assistant must say "not found" when the library does not support an answer.

---

## 10. Domain assumptions register

Every assumption the system relies on, with its current status and owner. **Proposed** means it still needs confirmation. Nothing marked Proposed should be presented as validated.

| # | Assumption | Status | Owner |
|---|---|---|---|
| A1 | Four indicators (resting heart rate, SpO2, sleep, body temperature) fit the data the generator can produce | Pending confirmation | Sofia |
| A2 | The 08:00 reading counts as resting by protocol | Defined | Ammara |
| A3 | 7-day rolling baseline for all indicators; days 1-7 are a calibration window | Defined | Ammara |
| A4 | Heart-rate baseline excludes readings that triggered an alert | Defined | Ammara, Elthiero to implement |
| A5 | Simulation ranges: HR 56-68 bpm, SpO2 96-99 %, sleep 6.5-7.5 h on normal nights | Defined for generator use only | Sofia |
| A6 | Skin-temperature simulation range | **Open** | Sofia |
| A7 | Core-temperature reference values, defined separately from skin | **Open** | Sofia |
| A8 | HR delta 15 bpm; SpO2 delta 3 points; sleep delta 1.5 h; sleep floor 6 h | Prototype values | Ammara |
| A9 | TEMP-01 delta of +0.5 °C | **Provisional**, review against sensor accuracy pending | Ammara, Sofia |
| A10 | Skin-temperature validity range 28-38 °C | **Proposed** | Sofia |
| A11 | Minimum 4-hour spacing for sustained skin-temperature deviation | **Proposed** | Sofia, Elthiero |
| A12 | Skin baseline is calculated per time window | **Proposed** | Elthiero |
| A13 | Core readings never enter the skin baseline | Defined | Elthiero, tested by Shubhi |
| A14 | API additions (`rule_id`, `unit`, `delta`, `category`, `next_step`, `source`, `baseline_status`, and for temperature `temp_type`, `sensor_location`, `device`, `measurement_method`) | **Needs agreement** because API contract v1 is frozen | Abdullah, Elthiero |
| A15 | Severity levels are operational, not clinical acuity | Defined | Ammara |
| A16 | NASA OSDR field accessibility | **Open** | Sofia |

---

## 11. Design and labelling rules

**Persistent labels (every screen and every export):** the violet SIMULATED banner and the line "Decision support only - not a medical diagnosis".

**Layout (from the team guide):** left sidebar (Dashboard, Health Alerts, AI Assistant, System Status); top bar with the SIMULATED DATA banner and online/offline pill; four metric cards; 14-day charts with a baseline line and alert markers; active-alerts panel.

### UI palette (dark theme)

| Hex | Name | Usage |
|---|---|---|
| `#0B132B` | Midnight Navy | Main background and canvas |
| `#1C2541` | Deep Slate Blue | Cards, sidebar, surfaces |
| `#3A506B` | Muted Steel Blue | Borders, dividers, inactive pills (never text) |
| `#FFD166` | Solar Gold | Active states, action buttons, warning highlights |
| `#FFFFFF` | Pure White | Headers, primary text, icons |
| `#8D99AE` | Cool Slate Gray | Secondary text, timestamps, inactive navigation |
| `#06D6A0` | Orbit Green | System status and telemetry (never a "normal" label for a health value) |

### Severity and status colours

| Element | Colour | Rule |
|---|---|---|
| NOTICE | Slate blue `#3B5BDB` | Filled badge, white text, always icon plus text label |
| WATCH | Amber `#B45309` | Filled badge, white text, always icon plus text label |
| ATTENTION | Deep orange-red `#C2410C` | Filled badge, white text; avoids pure red so it does not read as an emergency |
| Data quality or setup | Grey `#6B7280` | Filled badge, visually separate from physiological alerts |
| SIMULATED banner | Violet `#6D28D9` | On every screen and in exports |
| Offline pill | Orbit Green `#06D6A0` | Navy text, reads "Offline mode OK" |

Use severity colours as **filled badges**, not as coloured text on Midnight Navy, where amber and slate blue have low contrast. Solar Gold never replaces a severity tag.

---

## 12. Limitations and ethics

**Limitations**

- The data is simulated.
- The library is small (nine sources).
- Numeric triggers are prototype workflow rules without clinical validation.
- Rules based only on a personal baseline can miss a slow drift, because the baseline moves with the person.
- Skin temperature is not core temperature and depends on sensor placement, contact and conditions.
- Wearable proxies cannot diagnose immune dysfunction, radiation injury or bone loss.

**What we do not claim.** Clinical validation, diagnostic performance, real astronaut data, or proven prediction of any condition.

**Ethics and safe-use principles**

- Decision support only. The system supports an astronaut's own judgement and never gives a diagnosis.
- Every number is labelled SIMULATED and is never presented as real astronaut data.
- The assistant answers only from retrieved passages, cites title, journal, year and link, and says "not found" when evidence is missing.
- The assistant never infers a diagnosis, fever or immune condition from proxy indicators or skin temperature.
- Data-quality problems are reported as data problems, never as health events.

---

## 13. Open items and status

**Prepared:** indicator definitions, temperature strategy, baseline method, alert rules, alert card wording, design brief and palette, nine-source library, handoff notes.

**Pending:**

| Item | Owner | Needed for |
|---|---|---|
| Confirm simulation ranges, including skin temperature, and device quality checks | Sofia | Data generator |
| Define core-temperature reference values separately | Sofia | Manual core entry |
| Review TEMP-01 threshold against sensor accuracy and variability | Ammara, Sofia | Before TEMP-01 is implemented |
| Confirm 28-38 °C validity range and 4-hour spacing | Sofia, Elthiero | Valid-reading logic |
| Source access and licensing check (full text for S4 and S7) | Cesar | RAG ingestion |
| Agree the API field additions in A14 | Abdullah, Elthiero | Alert object and temperature storage |
| Re-verify DOIs for S8 and S9 and record the verification date | Ammara | `sources.csv` |
| Reviewed alert wording (14 Nov PM) | Ammara | Alert cards |
| Answer-accuracy review of the assistant's 10 test questions (15 Nov AM) | Ammara, Cesar | Assistant sign-off |

---

## 14. Review log

Add one row per review. Do not record a review as done until it has actually happened.

| Date | Item reviewed | Reviewer | Result | Changes made |
|---|---|---|---|---|
| 13 Nov 2026 | Deliverables pack v1 (indicators, rules, library, palette) | Ammara | Prepared | Handoff pack issued |
| 14 Nov 2026 (PM) | Alert wording on all eight rules | Ammara | Pending | - |
| 15 Nov 2026 (AM) | Assistant answers, 10 test questions including unsupported ones | Ammara, Cesar | Pending | - |

---

## 15. How each teammate uses this folder

| Teammate | What to take from here |
|---|---|
| **Abdullah** | Alert card order (Section 6), palette (Section 11), the "Skin temperature" card label, a separate manual core-entry form, baseline-not-established and data-quality states, and the limitations text (Section 12) for the main README |
| **Elthiero** | Implement the rules in Section 5 exactly. Keep DATA-01 and DATA-02 separate from physiological alerts. Store skin and core temperature separately. Make `temp_delta_threshold` configurable. Agree the API additions in A14 |
| **Cesar** | Ingest the nine sources by DOI (Section 8). Confirm full-text access for S4 and S7 and licensing first. Answers must cite only retrieved passages, say "not found" when evidence is missing, and never infer a diagnosis |
| **Sofia** | Confirm indicators, ranges and quality checks. Define skin and core ranges separately. Place planted anomalies on day 20 and days 24-26. Keep days 1-7 clean |
| **Shubhi** | Write normal, borderline and abnormal test cases for every rule ID. Test that core readings never enter the skin baseline. Check the SIMULATED badge, disclaimer and colour-independent severity on every screen |

---

## 16. Glossary

| Term | Meaning |
|---|---|
| **Baseline** | An individual's own recent average for an indicator (7-day rolling), used as the comparison point instead of a population range |
| **Calibration window** | Days 1-7, during which the baseline is being built and no personalised alerts fire |
| **Prototype rule** | A workflow trigger chosen by the team for the demo; not a clinically validated threshold |
| **Skin temperature** | Wearable-measured surface temperature; the primary temperature indicator |
| **Core temperature** | Deep-body temperature taken manually under protocol; confirmatory only |
| **Time window** | A part of the day (for example overnight or morning) used so skin temperature is compared like with like |
| **Sustained deviation** | A threshold exceedance that repeats across readings or days, as defined in Section 4 |
| **RAG** | Retrieval-augmented generation: the assistant answers from retrieved library passages |
| **Retrieval-only mode** | Fallback where the assistant shows cited excerpts without an LLM-written answer |
| **OSDR** | NASA Open Science Data Repository |
| **Provenance** | A record of where each rule and number comes from |

---

## 17. Files, licensing and credits

**Files in `library/`**

| File | Purpose |
|---|---|
| `README.md` | This document |
| `sources.csv` | Machine-readable source list for Cesar's ingestion |

**`sources.csv` columns:** `id, citation, year, journal, doi, pmid_or_pmcid, url, domain, relevance, limitation, access, license_status, used_for_rules, date_verified`

**Raw PDFs are not committed.** Per the team Git rules, they are shared through the team drive and listed here by source ID (S1-S9).

**Credits.** Sources S1-S9 are credited to their authors and publishers as cited in Section 8. NASA data and papers, and any AI tools and models used by the team, are disclosed in the main project README as the Space Apps rules require.

---

*Decision support only - not a medical diagnosis. All data in this project is SIMULATED.*
