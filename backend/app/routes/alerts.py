from fastapi import APIRouter, Depends

from app import config
from app.db.database import get_db
from app.utils import clean_number

router = APIRouter()


@router.get("/alerts")
def get_alerts(conn=Depends(get_db)):
    rows = conn.execute(
        "SELECT id, rule, severity, metric, value, baseline, ts, message FROM alerts "
        "WHERE astronaut_id = ? ORDER BY position ASC",
        (config.default_astronaut_id(),),
    ).fetchall()
    return {
        "alerts": [
            {
                "id": r["id"],
                "rule": r["rule"],
                "severity": r["severity"],
                "metric": r["metric"],
                "value": clean_number(r["value"]),
                "baseline": clean_number(r["baseline"]),
                "timestamp": r["ts"],
                "message": r["message"],
            }
            for r in rows
        ]
    }
