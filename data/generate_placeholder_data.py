"""Placeholder data generator (SIMULATED). Replace with Sofia's data when she delivers.

Creates `days` daily readings ending at `--end`, with two planted anomalies for the demo:
  * last day heart rate = 78 (baseline is about 62), so the heart-rate alert fires
  * last three nights of sleep are under 6 hours, so the sleep alert fires

Usage:
    python data/generate_placeholder_data.py                 # writes data/sample/readings.csv
    python data/generate_placeholder_data.py --days 14 --json contract/examples/readings.json
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["timestamp", "heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c"]


def generate(days=30, end="2026-11-14T08:00:00Z", seed=42):
    rng = random.Random(seed)
    end_dt = datetime.strptime(end, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    rows = []
    for i in range(days):
        ts = end_dt - timedelta(days=days - 1 - i)
        rows.append({
            "timestamp": ts.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "heart_rate_bpm": rng.choice([60, 61, 62, 62, 63, 64]),
            "spo2_pct": rng.choice([96, 97, 97, 98]),
            "sleep_hours": round(rng.uniform(6.4, 7.4), 1),
            "body_temp_c": round(rng.uniform(36.5, 36.8), 1),
        })
    rows[-1]["heart_rate_bpm"] = 78
    for row, hours in zip(rows[-3:], (5.7, 5.5, 5.8)):
        row["sleep_hours"] = hours
    return rows


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--end", default="2026-11-14T08:00:00Z")
    ap.add_argument("--csv", default=str(ROOT / "data" / "sample" / "readings.csv"))
    ap.add_argument("--json", help="also write the {data_label, readings} JSON used by the contract examples")
    args = ap.parse_args()
    rows = generate(args.days, args.end)
    if args.json:
        Path(args.json).write_text(json.dumps({"data_label": "SIMULATED", "readings": rows}, indent=2) + "\n")
    else:
        Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
        with open(args.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
    print(f"wrote {len(rows)} rows")
