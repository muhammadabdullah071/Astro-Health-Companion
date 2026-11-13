"""Placeholder data generator (SIMULATED). Replace with Sofia's data when she delivers.

Follows Ammara's demo scenario on a 26 day dataset (day 1 is the first row):
  * days 1 to 7 are clean (they form the baseline calibration window)
  * day 20: heart rate 78 bpm against a baseline near 62, about +16 bpm (HR-01 fires)
  * days 24 to 26: sleep under 6 hours (SLEEP-01 fires)
  * body_temp_c is SKIN temperature (placeholder range 33.3 to 33.7 C, Sofia sets the real one)
Simulation ranges (Ammara Section 2): heart rate 56 to 68, SpO2 96 to 99, sleep 6.5 to 7.5 h.

Usage:
    python data/generate_placeholder_data.py                                  # writes data/sample/readings.csv
    python data/generate_placeholder_data.py --last 14 --json contract/examples/readings.json
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = [
    "timestamp", "heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c",
    "hr_quality", "spo2_quality", "sleep_source",
    "temp_sensor_location", "temp_device_id", "temp_contact_quality", "temp_dropout",
]
CORE = FIELDS[:5]


def generate(days=26, end="2026-11-14T08:00:00Z", seed=42):
    rng = random.Random(seed)
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    rows = []
    for i in range(days):
        ts = end_dt - timedelta(days=days - 1 - i)
        rows.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "heart_rate_bpm": rng.choice([60, 61, 62, 62, 63, 64]),
            "spo2_pct": rng.choice([96, 97, 97, 98, 99]),
            "sleep_hours": round(rng.uniform(6.5, 7.5), 1),
            "body_temp_c": round(rng.uniform(33.3, 33.7), 1),
            "hr_quality": "good",
            "spo2_quality": "good",
            "sleep_source": "wearable",
            "temp_sensor_location": "wrist",
            "temp_device_id": "wearable-01",
            "temp_contact_quality": "good",
            "temp_dropout": 0,
        })
    if days >= 20:
        # pin days 13 to 19 (the baseline window before the anomaly) so the demo reads +16 bpm
        for row, hr in zip(rows[12:19], (61, 62, 62, 63, 61, 62, 62)):
            row["heart_rate_bpm"] = hr
        rows[19]["heart_rate_bpm"] = 78                       # day 20
    for day, hours in zip((24, 25, 26), (5.7, 5.5, 5.8)):     # days 24 to 26
        if day <= days:
            rows[day - 1]["sleep_hours"] = hours
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=26)
    ap.add_argument("--end", default="2026-11-14T08:00:00Z")
    ap.add_argument("--csv", default=str(ROOT / "data" / "sample" / "readings.csv"))
    ap.add_argument("--json", help="write {data_label, readings} JSON for the contract examples instead of the CSV")
    ap.add_argument("--last", type=int, help="with --json: keep only the last N rows")
    args = ap.parse_args()
    rows = generate(args.days, args.end)
    if args.json:
        keep = rows[-args.last:] if args.last else rows
        out = [{k: r[k] for k in CORE} for r in keep]
        Path(args.json).write_text(json.dumps({"data_label": "SIMULATED", "readings": out}, indent=2) + "\n")
        print(f"wrote {len(out)} rows to {args.json}")
    else:
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {len(rows)} rows to {args.csv}")
