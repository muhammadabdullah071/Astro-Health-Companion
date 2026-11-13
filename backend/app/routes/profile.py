from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends

from app import config
from app.db.database import get_db
from app.engine.rules_config import BASELINE_DAYS
from app.errors import AppError
from app.utils import parse_ts

router = APIRouter()


@router.get("/profile")
def get_profile(conn=Depends(get_db)):
    astro_id = config.default_astronaut_id()
    row = conn.execute("SELECT * FROM profile WHERE id = ?", (astro_id,)).fetchone()
    if not row:
        raise AppError(404, "NOT_FOUND", "Profile not found.")
    latest = conn.execute("SELECT MAX(ts) FROM readings WHERE astronaut_id = ?", (astro_id,)).fetchone()[0]
    ref = parse_ts(latest).date() if latest else datetime.now(timezone.utc).date()
    start = date.fromisoformat(row["mission_start_date"])
    return {
        "id": row["id"],
        "name": row["name"],
        "mission": row["mission"],
        "mission_day": (ref - start).days + 1,
        "baseline_window_days": BASELINE_DAYS,
        "data_label": row["data_label"],
    }
