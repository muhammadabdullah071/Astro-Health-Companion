"""Create and fill the SQLite database. Safe to run again: it rebuilds everything.

Usage (from the backend folder):
    python -m app.db.seed
    python -m app.db.seed --csv ../data/sample/readings.csv --traceability ../data/sample/traceability.csv

Data source order:
  1. --csv (one profile, stored as ASTRO_ID; add --traceability for the quality sidecar)
  2. data/sample/manifest.json (Sofia's delivery): every profile it lists, each with its own CSV,
     plus the quality sidecar (traceability.csv) that makes DATA-01 possible
  3. data/sample/readings.csv alone, then contract/examples/readings.json as a last resort

Readings CSV needs: timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c (body_temp_c = SKIN temperature).
Quality values come from, in order: optional columns in the CSV itself, the traceability sidecar, the defaults.
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

# Sofia's traceability.csv column -> readings table column
TRACE_TO_COLUMN = {
    "heart_rate_quality": "hr_quality",
    "spo2_quality": "spo2_quality",
    "temperature_quality": "temp_contact_quality",
    "temperature_site": "temp_sensor_location",
    "temperature_device_id": "temp_device_id",
}

DEFAULT_START_DATE = "2026-10-16"   # first reading of the sample data, so mission day matches Sofia's mission_day
PROFILE = {"mission": "Simulated long-duration mission", "data_label": config.DATA_LABEL}


def _to_float(v):
    if v is None or str(v).strip() == "":
        return None
    return float(v)


def _blank(v):
    return v is None or str(v).strip() == ""


def _extra(raw, key, sidecar):
    v = raw.get(key)
    if _blank(v):
        v = sidecar.get(key, QUALITY_DEFAULTS[key])
    return int(float(v)) if key == "temp_dropout" else str(v).strip()


def _row(raw, sidecar=None):
    sidecar = sidecar or {}
    return {
        "timestamp": raw["timestamp"].strip(),
        **{m: _to_float(raw.get(m)) for m in METRICS},
        **{k: _extra(raw, k, sidecar) for k in EXTRAS},
    }


def load_traceability(path, profile_id):
    """timestamp -> quality columns for ONE profile from Sofia's traceability.csv."""
    out = {}
    with Path(path).open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r.get("profile_id") != profile_id:
                continue
            out[r["timestamp"].strip()] = {
                column: r[source].strip() for source, column in TRACE_TO_COLUMN.items() if not _blank(r.get(source))
            }
    return out


def load_rows(csv_path=None, sidecar=None):
    """Readings from a CSV (default sample CSV), or from the contract example JSON as a last resort."""
    path = Path(csv_path) if csv_path else config.sample_csv_path()
    sidecar = sidecar or {}
    if path.exists():
        with path.open(newline="", encoding="utf-8") as f:
            rows = [_row(r, sidecar.get(r["timestamp"].strip())) for r in csv.DictReader(f)]
    else:
        data = json.loads((config.examples_dir() / "readings.json").read_text(encoding="utf-8"))
        rows = [_row(r) for r in data["readings"]]
    if not rows:
        raise ValueError("No readings found to seed the database.")
    return sorted(rows, key=lambda r: r["timestamp"])


def load_dataset(csv_path=None, traceability_path=None):
    """Returns ({profile_id: rows}, mission_start_date)."""
    if csv_path:
        pid = config.default_astronaut_id()
        sidecar = load_traceability(traceability_path, pid) if traceability_path else {}
        return {pid: load_rows(csv_path, sidecar)}, DEFAULT_START_DATE

    manifest_path = config.sample_csv_path().parent / "manifest.json"
    if manifest_path.exists():
        base = manifest_path.parent
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        trace_name = manifest.get("traceability_file")
        trace_file = base / trace_name if trace_name else None
        dataset = {}
        for p in manifest["profiles"]:
            sidecar = load_traceability(trace_file, p["profile_id"]) if trace_file and trace_file.exists() else {}
            dataset[p["profile_id"]] = load_rows(base / p["csv"], sidecar)
        return dataset, manifest.get("first_date", DEFAULT_START_DATE)

    return {config.default_astronaut_id(): load_rows()}, DEFAULT_START_DATE


def seed(csv_path=None, traceability_path=None) -> dict:
    dataset, start_date = load_dataset(csv_path, traceability_path)
    default_id = config.default_astronaut_id()
    if default_id not in dataset:
        raise ValueError(f"ASTRO_ID {default_id!r} is not in the dataset (found: {', '.join(dataset)})")
    conn = database.connect()
    try:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        placeholders = ", ".join("?" * (2 + len(COLUMNS)))
        for pid, rows in dataset.items():
            conn.execute(
                "INSERT INTO profile (id, name, mission, mission_start_date, data_label) VALUES (?, ?, ?, ?, ?)",
                (pid, f"Simulated astronaut {pid}", PROFILE["mission"], start_date, PROFILE["data_label"]),
            )
            conn.executemany(
                f"INSERT INTO readings (astronaut_id, ts, {', '.join(COLUMNS)}) VALUES ({placeholders})",
                [(pid, r["timestamp"], *[r[c] for c in COLUMNS]) for r in rows],
            )
        conn.commit()
        profiles = {pid: {"readings": len(rows), "alerts": len(service.recompute_alerts(conn, pid))}
                    for pid, rows in dataset.items()}
    finally:
        conn.close()
    return {"astronaut_id": default_id, **profiles[default_id], "profiles": profiles, "db": str(config.db_path())}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Seed the Astro-Health database")
    ap.add_argument("--csv", help="one readings CSV (stored as ASTRO_ID)")
    ap.add_argument("--traceability", help="quality sidecar CSV (Sofia's traceability.csv)")
    args = ap.parse_args()
    print(seed(Path(args.csv) if args.csv else None, Path(args.traceability) if args.traceability else None))
