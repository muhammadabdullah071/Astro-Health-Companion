"""Glue between the database and the pure rule functions."""
from __future__ import annotations

from app import config
from app.engine import rules

METRICS = ("heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c")


def load_series(conn, astronaut_id):
    cur = conn.execute(
        "SELECT ts, heart_rate_bpm, spo2_pct, sleep_hours, body_temp_c FROM readings "
        "WHERE astronaut_id = ? ORDER BY ts ASC",
        (astronaut_id,),
    )
    return [{"timestamp": r["ts"], **{m: r[m] for m in METRICS}} for r in cur.fetchall()]


def recompute_alerts(conn, astronaut_id=None):
    """Rebuild the alerts table from the latest reading. Returns the stored alerts."""
    astronaut_id = astronaut_id or config.default_astronaut_id()
    series = load_series(conn, astronaut_id)
    alerts = rules.evaluate(series)
    conn.execute("DELETE FROM alerts WHERE astronaut_id = ?", (astronaut_id,))
    conn.executemany(
        "INSERT INTO alerts (id, astronaut_id, position, rule_id, rule, severity, metric, value, baseline, ts, "
        "message, next_step, source) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (a["id"], astronaut_id, a["position"], a["rule_id"], a["rule"], a["severity"], a["metric"],
             a["value"], a["baseline"], a["timestamp"], a["message"], a["next_step"], a["source"])
            for a in alerts
        ],
    )
    conn.commit()
    return alerts


def fetch_alert(conn, alert_id, astronaut_id=None):
    astronaut_id = astronaut_id or config.default_astronaut_id()
    row = conn.execute(
        "SELECT id, rule_id, rule, severity, metric, value, baseline, ts AS timestamp, message, next_step, source "
        "FROM alerts WHERE id = ? AND astronaut_id = ?",
        (alert_id, astronaut_id),
    ).fetchone()
    return dict(row) if row else None
