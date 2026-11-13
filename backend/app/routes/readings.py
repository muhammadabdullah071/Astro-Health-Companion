from fastapi import APIRouter, Depends, Query

from app import config
from app.db.database import get_db
from app.utils import clean_number

router = APIRouter()


@router.get("/readings")
def get_readings(days: int = Query(14, ge=1, le=90), conn=Depends(get_db)):
    """Last `days` readings relative to the newest reading (not the wall clock), oldest first."""
    rows = conn.execute(
        "SELECT ts, heart_rate_bpm, spo2_pct, sleep_hours, body_temp_c FROM ("
        "  SELECT * FROM readings WHERE astronaut_id = ? ORDER BY ts DESC LIMIT ?"
        ") ORDER BY ts ASC",
        (config.default_astronaut_id(), days),
    ).fetchall()
    return {
        "data_label": config.DATA_LABEL,
        "readings": [
            {
                "timestamp": r["ts"],
                "heart_rate_bpm": clean_number(r["heart_rate_bpm"]),
                "spo2_pct": clean_number(r["spo2_pct"]),
                "sleep_hours": clean_number(r["sleep_hours"]),
                "body_temp_c": clean_number(r["body_temp_c"]),
            }
            for r in rows
        ],
    }
