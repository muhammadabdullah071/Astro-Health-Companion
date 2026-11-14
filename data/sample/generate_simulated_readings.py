#!/usr/bin/env python3
"""Generate 30 days of explicitly SIMULATED Astro-Health Companion data.

The five-column CSV preserves Elthiero's frozen import schema. Per-profile
files prevent ambiguous duplicate timestamps. An additional traceability CSV
retains provenance, data quality, scenario IDs and measurement semantics.

All physiological values and anomalies are synthetic engineering scenarios.
They are not real astronaut observations or clinically validated ranges.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HEADERS = ("timestamp", "heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c")
TRACE_HEADERS = (
    "profile_id", "mission_day", "timestamp", "data_label", "anomaly_id",
    "heart_rate_quality", "spo2_quality", "sleep_quality", "temperature_quality",
    "temperature_type", "temperature_site", "temperature_device_id", "temperature_time_window",
    "sleep_attribution", "note",
)
SEED = 20261113
START_DATE = date(2026, 10, 16)
DAYS = 30
# Synthetic skin-temperature baseline choices; see DATA_SHEET.md for their provenance.
SKIN_TEMPERATURE_BASELINES = {
    "ASTRO-01": 33.2,
    "ASTRO-02": 33.4,
}
PROFILE_SETTINGS = {
    "ASTRO-01": {"hr": 62, "spo2": 97, "sleep": 7.0},
    "ASTRO-02": {"hr": 65, "spo2": 98, "sleep": 7.2},
}


def write_csv(path: Path, headers: tuple[str, ...], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def timestamp_for_day(first_day: date, mission_day: int) -> str:
    time = datetime.combine(first_day + timedelta(days=mission_day - 1), datetime.min.time(), tzinfo=timezone.utc)
    return time.replace(hour=8).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_profile(profile_id: str, first_day: date, days: int, rng: random.Random):
    """Create one profile without mixing subject identities into import columns."""
    cfg = PROFILE_SETTINGS[profile_id]
    readings: list[dict] = []
    traceability: list[dict] = []

    for day in range(1, days + 1):
        timestamp = timestamp_for_day(first_day, day)
        hr = cfg["hr"] + rng.choice((-2, -1, 0, 0, 0, 1, 2))
        spo2 = max(96, min(99, cfg["spo2"] + rng.choice((-1, 0, 0, 0, 1))))
        sleep = round(max(6.5, min(7.5, cfg["sleep"] + rng.choice((-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3)))), 1)
        skin_temp = round(SKIN_TEMPERATURE_BASELINES[profile_id] + rng.choice((-0.2, -0.1, 0.0, 0.0, 0.1, 0.2)), 1)
        anomaly_id = ""
        spo2_quality = "good"
        note = ""

        if profile_id == "ASTRO-01":
            # Fix the 7 valid days immediately BEFORE day 20 to average 62 bpm.
            hr_reference = {13: 60, 14: 61, 15: 62, 16: 63, 17: 64, 18: 62, 19: 62}
            if day in hr_reference:
                hr = hr_reference[day]
            # The 7 pre-event sleep nights (days 17-23) average exactly 7.0 h.
            sleep_reference = {17: 6.9, 18: 7.1, 19: 7.0, 20: 6.8, 21: 7.2, 22: 7.1, 23: 6.9}
            if day in sleep_reference:
                sleep = sleep_reference[day]
            # Establish 97% as the preceding seven-day SpO2 baseline for the isolated dip.
            if 15 <= day <= 21:
                spo2 = 97
            if day == 20:
                hr, anomaly_id = 78, "HR_DAY20"
                note = "HR-01 demonstration: 78 bpm versus prior 7-day baseline of 62 bpm"
            if day == 22:
                spo2, spo2_quality, anomaly_id = 93, "poor", "ISOLATED_SPO2_QUALITY"
                note = "One isolated, poor-quality SpO2 reading; NOT a SPO2-01 physiological alert"
            if day in (24, 25, 26):
                sleep = {24: 5.4, 25: 5.6, 26: 5.2}[day]
                anomaly_id = "SLEEP_DAYS24_26"
                note = "Three-night reduced-sleep scenario; SLEEP-01 evaluates on day 26"

        readings.append({
            "timestamp": timestamp,
            "heart_rate_bpm": hr,
            "spo2_pct": spo2,
            "sleep_hours": sleep,
            # Legacy API name; this is SKIN temperature, not core temperature.
            "body_temp_c": skin_temp,
        })
        traceability.append({
            "profile_id": profile_id,
            "mission_day": day,
            "timestamp": timestamp,
            "data_label": "SIMULATED",
            "anomaly_id": anomaly_id,
            "heart_rate_quality": "good",
            "spo2_quality": spo2_quality,
            "sleep_quality": "good",
            "temperature_quality": "good",
            "temperature_type": "skin",
            "temperature_site": "left_wrist",
            "temperature_device_id": "SIM-WEARABLE-01",
            "temperature_time_window": "08:00_UTC_morning",
            "sleep_attribution": "previous_sleep_ending_on_record_date",
            "note": note,
        })

    return readings, traceability


def validate(readings: list[dict], trace: list[dict], first_day: date, days: int, is_primary: bool) -> None:
    assert len(readings) == days == len(trace), "Missing or extra records"
    assert all(tuple(row) == HEADERS for row in readings), "Import schema changed"
    assert len({r["timestamp"] for r in readings}) == days, "Duplicate timestamp within profile"
    assert all(t["data_label"] == "SIMULATED" for t in trace), "Provenance label missing"
    assert [r["timestamp"] for r in readings] == [timestamp_for_day(first_day, d) for d in range(1, days + 1)]
    assert all(28 <= r["body_temp_c"] <= 38 for r in readings), "Outside specified simulation validity screen"
    assert all(not trace[d]["anomaly_id"] for d in range(7)), "First 7 days must be clean"
    if is_primary and days >= 26:
        hr_base = sum(r["heart_rate_bpm"] for r in readings[12:19]) / 7
        sleep_pre_event_base = sum(r["sleep_hours"] for r in readings[16:23]) / 7
        assert hr_base == 62 and readings[19]["heart_rate_bpm"] == 78, "HR demo scenario drifted"
        assert abs(sleep_pre_event_base - 7.0) < 1e-9, "Sleep demo reference drifted"
        assert [r["sleep_hours"] for r in readings[23:26]] == [5.4, 5.6, 5.2]
        assert readings[21]["spo2_pct"] == 93 and trace[21]["spo2_quality"] == "poor"
        assert readings[22]["spo2_pct"] >= 96, "Isolated dip must not persist"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reproducible SIMULATED astronaut data")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "generated_data")
    parser.add_argument("--profiles", type=int, default=2, choices=(1, 2))
    parser.add_argument("--days", type=int, default=DAYS, help="Use 30 for the documented demo scenarios")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--start-date", type=date.fromisoformat, default=START_DATE)
    args = parser.parse_args()
    if args.days < 26:
        parser.error("At least 26 days are needed for the documented demo scenarios")
    args.out.mkdir(parents=True, exist_ok=True)

    all_trace: list[dict] = []
    manifest: list[dict] = []
    for index, profile_id in enumerate(list(PROFILE_SETTINGS)[:args.profiles], start=1):
        # Each profile gets its own independent deterministic random stream.
        rng = random.Random(args.seed + index)
        readings, trace = make_profile(profile_id, args.start_date, args.days, rng)
        validate(readings, trace, args.start_date, args.days, index == 1)
        stem = "readings" if index == 1 else f"readings_profile_{index:02}"
        csv_name, json_name = stem + ".csv", stem + ".json"
        write_csv(args.out / csv_name, HEADERS, readings)
        write_json(args.out / json_name, {"data_label": "SIMULATED", "readings": readings})
        all_trace.extend(trace)
        manifest.append({"profile_id": profile_id, "csv": csv_name, "json": json_name, "records": len(readings)})

    write_csv(args.out / "traceability.csv", TRACE_HEADERS, all_trace)
    write_json(args.out / "manifest.json", {
        "data_label": "SIMULATED",
        "generator_seed": args.seed,
        "first_date": args.start_date.isoformat(),
        "last_date": (args.start_date + timedelta(days=args.days - 1)).isoformat(),
        "sleep_timestamp_meaning": "Sleep ending at 08:00 UTC on day N is assigned to day N",
        "body_temp_c_meaning": "SIMULATED wearable skin temperature at the left wrist, NOT core temperature",
        "temperature_semantics": "body_temp_c is the frozen import column; skin temperature is the primary monitored metric; core measurements are not generated",
        "provenance": "SIMULATED engineering values based on internal team design; NOT NASA astronaut measurements",
        "profiles": manifest,
        "traceability_file": "traceability.csv",
        "expected_alerts_file": "expected_alerts.json",
        "simulation_model": "Illustrative wrist skin-temperature baselines; not clinical reference ranges or sensor-calibrated values",
    })

    if args.days == 30:
        t = lambda day: timestamp_for_day(args.start_date, day)
        fixtures = {
            "data_label": "SIMULATED",
            "note": "Reference outcomes for the documented SIMULATED scenarios using Ammara's prototype rules. Not medical thresholds.",
            "expected_events": [
                {"profile_id": "ASTRO-01", "mission_day": 1, "timestamp": t(1), "rule_id": "DATA-02", "expected": True, "reason": "Fewer than 7 usable preceding/calibration readings"},
                {"profile_id": "ASTRO-01", "mission_day": 20, "timestamp": t(20), "rule_id": "HR-01", "expected": True, "severity": "WATCH", "value": 78, "baseline": 62, "delta": 16, "unit": "bpm"},
                {"profile_id": "ASTRO-01", "mission_day": 20, "timestamp": t(20), "rule_id": "HR-02", "expected": False, "reason": "Only one elevated daily HR observation"},
                {"profile_id": "ASTRO-01", "mission_day": 22, "timestamp": t(22), "rule_id": "SPO2-01", "expected": False, "reason": "One isolated dip, additionally marked poor-quality in sidecar"},
                {"profile_id": "ASTRO-01", "mission_day": 22, "timestamp": t(22), "rule_id": "DATA-01", "expected": True, "requires": "spo2_quality from traceability.csv", "reason": "Poor signal-quality flag, not a physiological inference"},
                {"profile_id": "ASTRO-01", "mission_day": 26, "timestamp": t(26), "rule_id": "SLEEP-01", "expected": True, "severity": "NOTICE", "readings": [5.4, 5.6, 5.2], "unit": "h"},
                {"profile_id": "ASTRO-01", "mission_day": 26, "timestamp": t(26), "rule_id": "SLEEP-02", "expected": False, "reason": "Only day 24 exceeds 1.5 hours below its preceding rolling 7-night baseline; not three consecutive qualifying nights"},
            ],
            "fixture_conventions": ["Daily baselines use the previous seven valid comparable readings, excluding the current reading", "DATA-01 requires the optional quality information in traceability.csv", "Skin and core temperatures must never be combined"],
        }
        write_json(args.out / "expected_alerts.json", fixtures)
    print(f"Generated {args.profiles} profile(s), {args.days} days each in {args.out}")
    print("Import readings.csv first for ASTRO-01; import readings_profile_02.csv separately for ASTRO-02.")
    print("body_temp_c represents SIMULATED wrist skin temperature (not core temperature).")


if __name__ == "__main__":
    main()
