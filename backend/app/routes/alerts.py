from fastapi import APIRouter, Depends, Query

from app import config
from app.db.database import get_db
from app.engine import service
from app.utils import clean_number

router = APIRouter()

SELECT = (
    "SELECT id, rule_id, rule, severity, category, metric, value, unit, baseline, delta, baseline_status, "
    "ts, message, next_step, source, data_quality, temp_type, sensor_location, device, measurement_method "
    "FROM alerts WHERE astronaut_id = ? AND ts >= ? ORDER BY position ASC"
)


def _shape(a):
    """One alert as the contract describes it. `a` is a dict with a `timestamp` key."""
    return {
        "id": a["id"],
        "rule_id": a["rule_id"],
        "rule": a["rule"],
        "severity": a["severity"],
        "category": a["category"],
        "metric": a["metric"],
        "value": clean_number(a["value"]),
        "unit": a["unit"],
        "baseline": clean_number(a["baseline"]),
        "delta": clean_number(a["delta"]),
        "baseline_status": a["baseline_status"],
        "timestamp": a["timestamp"],
        "message": a["message"],
        "next_step": a["next_step"],
        "source": a["source"],
        "data_quality": a["data_quality"],
        "data_label": config.DATA_LABEL,
        "temp_type": a["temp_type"],
        "sensor_location": a["sensor_location"],
        "device": a["device"],
        "measurement_method": a["measurement_method"],
    }


@router.get("/alerts")
def get_alerts(days: int = Query(14, ge=1, le=90), conn=Depends(get_db)):
    """Alerts raised within the last `days` readings (same window as /api/readings), most severe first.

    When STALE_CHECK is on and the newest reading is too old, a request-time DATA-01 notice (id "s1") is
    added. It is a notice, so it goes in front of the other notices and behind every watch/attention alert.
    """
    astro = config.default_astronaut_id()
    cutoff = conn.execute(
        "SELECT MIN(ts) FROM (SELECT ts FROM readings WHERE astronaut_id = ? ORDER BY ts DESC LIMIT ?)",
        (astro, days),
    ).fetchone()[0] or ""
    rows = conn.execute(SELECT, (astro, cutoff)).fetchall()
    alerts = [_shape({**dict(r), "timestamp": r["ts"]}) for r in rows]
    stale = service.current_stale_alert(conn, astro)
    if stale:
        at = next((i for i, a in enumerate(alerts) if a["severity"] == "notice"), len(alerts))
        alerts.insert(at, _shape(stale))
    return {"alerts": alerts}
