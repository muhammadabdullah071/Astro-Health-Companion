from fastapi import APIRouter, Depends, Query

from app import config
from app.db.database import get_db
from app.utils import clean_number

router = APIRouter()

SELECT = (
    "SELECT id, rule_id, rule, severity, category, metric, value, unit, baseline, delta, baseline_status, "
    "ts, message, next_step, source, data_quality, temp_type, sensor_location, device, measurement_method "
    "FROM alerts WHERE astronaut_id = ? AND ts >= ? ORDER BY position ASC"
)


@router.get("/alerts")
def get_alerts(days: int = Query(14, ge=1, le=90), conn=Depends(get_db)):
    """Alerts raised within the last `days` readings (same window as /api/readings), most severe first."""
    astro = config.default_astronaut_id()
    cutoff = conn.execute(
        "SELECT MIN(ts) FROM (SELECT ts FROM readings WHERE astronaut_id = ? ORDER BY ts DESC LIMIT ?)",
        (astro, days),
    ).fetchone()[0] or ""
    rows = conn.execute(SELECT, (astro, cutoff)).fetchall()
    return {
        "alerts": [
            {
                "id": r["id"],
                "rule_id": r["rule_id"],
                "rule": r["rule"],
                "severity": r["severity"],
                "category": r["category"],
                "metric": r["metric"],
                "value": clean_number(r["value"]),
                "unit": r["unit"],
                "baseline": clean_number(r["baseline"]),
                "delta": clean_number(r["delta"]),
                "baseline_status": r["baseline_status"],
                "timestamp": r["ts"],
                "message": r["message"],
                "next_step": r["next_step"],
                "source": r["source"],
                "data_quality": r["data_quality"],
                "data_label": config.DATA_LABEL,
                "temp_type": r["temp_type"],
                "sensor_location": r["sensor_location"],
                "device": r["device"],
                "measurement_method": r["measurement_method"],
            }
            for r in rows
        ]
    }
