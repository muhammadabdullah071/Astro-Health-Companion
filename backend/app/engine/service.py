"""Glue between the database and the pure rule functions."""
from __future__ import annotations

from app import config
from app.engine import rules
from app.engine.quality import QUALITY_DEFAULTS

METRICS = ("heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c")
READING_COLUMNS = METRICS + tuple(QUALITY_DEFAULTS)

ALERT_COLUMNS = (
    "id", "astronaut_id", "position", "rule_id", "rule", "severity", "category", "metric", "value", "unit",
    "baseline", "delta", "baseline_status", "ts", "message", "next_step", "source", "data_quality",
    "temp_type", "sensor_location", "device", "measurement_method",
)


def load_series(conn, astronaut_id):
    cur = conn.execute(
        f"SELECT ts, {', '.join(READING_COLUMNS)} FROM readings WHERE astronaut_id = ? ORDER BY ts ASC",
        (astronaut_id,),
    )
    return [{"timestamp": r["ts"], **{c: r[c] for c in READING_COLUMNS}} for r in cur.fetchall()]


def recompute_alerts(conn, astronaut_id=None):
    """Rebuild the alerts table from ALL readings (history). Returns the stored alerts."""
    astronaut_id = astronaut_id or config.default_astronaut_id()
    alerts = rules.evaluate_all(load_series(conn, astronaut_id))
    conn.execute("DELETE FROM alerts WHERE astronaut_id = ?", (astronaut_id,))
    rows = []
    for a in alerts:
        a = {**a, "astronaut_id": astronaut_id, "ts": a["timestamp"]}
        rows.append(tuple(a[c] for c in ALERT_COLUMNS))
    conn.executemany(
        f"INSERT INTO alerts ({', '.join(ALERT_COLUMNS)}) VALUES ({', '.join('?' * len(ALERT_COLUMNS))})",
        rows,
    )
    conn.commit()
    return alerts


def fetch_alert(conn, alert_id, astronaut_id=None):
    """The full alert (including rule_id, next_step, source) for the assistant."""
    astronaut_id = astronaut_id or config.default_astronaut_id()
    row = conn.execute(
        "SELECT * FROM alerts WHERE id = ? AND astronaut_id = ?", (alert_id, astronaut_id)
    ).fetchone()
    if not row:
        return None
    alert = dict(row)
    alert["timestamp"] = alert.pop("ts")
    return alert
