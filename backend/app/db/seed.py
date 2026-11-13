"""Create and fill the SQLite database. Safe to run again: it rebuilds everything.

Usage (from the backend folder):
    python -m app.db.seed
    python -m app.db.seed --csv ../data/sample/readings.csv

Data source order:
  1. the CSV given with --csv (or ASTRO_SAMPLE_CSV)
  2. data/sample/readings.csv (placeholder data until Sofia delivers hers)
  3. contract/examples/readings.json (last resort)

The CSV needs: timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c (body_temp_c = SKIN temperature).
Optional quality columns (blank or missing means the default): hr_quality, spo2_quality, sleep_source,
temp_sensor_location, temp_device_id, temp_contact_quality, temp_dropout.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app import config
from app.db import database
from app.engine import service
from app.engine.quality import QUALITY_DEFAULTS

SCHEMA = Path(__file__).with_name("schema.sql")
METRICS = ("heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c")
EXTRAS = tuple(QUALITY_DEFAULTS)
COLUMNS = METRICS + EXTRAS

PROFILE = {
    "name": "Demo Astronaut A",
    "mission": "Simulated long-duration mission",
    "mission_start_date": "2026-06-25",
    "data_label": config.DATA_LABEL,
}


def _to_float(v):
    if v is None or str(v).strip() == "":
        return None
    return float(v)


def _extra(raw, key):
    v = raw.get(key)
    if v is None or str(v).strip() == "":
        return QUALITY_DEFAULTS[key]
    return int(float(v)) if key == "temp_dropout" else str(v).strip()


def _row(raw):
    return {
        "timestamp": raw["timestamp"],
        **{m: _to_float(raw.get(m)) for m in METRICS},
        **{k: _extra(raw, k) for k in EXTRAS},
    }


def load_rows(csv_path: Path | None = None) -> list[dict]:
    path = Path(csv_path) if csv_path else config.sample_csv_path()
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            rows = [_row(r) for r in csv.DictReader(f)]
    else:
        data = json.loads((config.examples_dir() / "readings.json").read_text(encoding="utf-8"))
        rows = [_row(r) for r in data["readings"]]
    if not rows:
        raise ValueError("No readings found to seed the database.")
    return sorted(rows, key=lambda r: r["timestamp"])


def seed(csv_path: Path | None = None) -> dict:
    rows = load_rows(csv_path)
    astro_id = config.default_astronaut_id()
    conn = database.connect()
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO profile (id, name, mission, mission_start_date, data_label) "
            "VALUES (:id, :name, :mission, :mission_start_date, :data_label)",
            {**PROFILE, "id": astro_id},
        )
        placeholders = ", ".join("?" * (2 + len(COLUMNS)))
        conn.executemany(
            f"INSERT INTO readings (astronaut_id, ts, {', '.join(COLUMNS)}) VALUES ({placeholders})",
            [(astro_id, r["timestamp"], *[r[c] for c in COLUMNS]) for r in rows],
        )
        conn.commit()
        alerts = service.recompute_alerts(conn, astro_id)
    finally:
        conn.close()
    return {"readings": len(rows), "alerts": len(alerts), "db": str(config.db_path())}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Seed the Astro-Health database")
    ap.add_argument("--csv", help="CSV with timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c")
    args = ap.parse_args()
    print(seed(Path(args.csv) if args.csv else None))
