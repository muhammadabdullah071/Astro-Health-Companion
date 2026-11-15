"""Manual CORE temperature entry (additive to contract v1, see docs/api-contract.md).

Stored in its own table. It is never used in the skin-temperature baseline, never creates an alert and
never produces a fever label: this endpoint only records and returns what the astronaut or medical officer typed.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app import config
from app.db.database import get_db
from app.errors import AppError
from app.utils import clean_number

router = APIRouter()

DISCLAIMER = ("Manual core-temperature entries are stored separately and are not used for skin-temperature "
              "baselines or alerts. This is not a diagnosis.")
TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
FUTURE_SKEW = timedelta(minutes=5)
CORE_MIN_C, CORE_MAX_C = 30.0, 45.0   # plausible physical range, a typo guard and not a clinical threshold


class CoreTemperatureBody(BaseModel):
    core_temp_c: float = Field(ge=CORE_MIN_C, le=CORE_MAX_C)
    method: Literal["oral", "tympanic", "temporal", "axillary", "rectal", "other"]
    timestamp: Optional[str] = None          # when it was measured; defaults to now (UTC)
    note: Optional[str] = Field(default=None, max_length=200)


def _measured_at(raw: Optional[str], now: datetime) -> datetime:
    if raw is None:
        return now
    try:
        parsed = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    except ValueError:
        raise AppError(422, "VALIDATION_ERROR", "Invalid request: timestamp must be ISO 8601 UTC, e.g. 2026-11-14T09:30:00Z.")
    if parsed.tzinfo is None:
        raise AppError(422, "VALIDATION_ERROR", "Invalid request: timestamp needs a UTC marker (Z) or offset.")
    parsed = parsed.astimezone(timezone.utc)
    if parsed > now + FUTURE_SKEW:
        raise AppError(422, "VALIDATION_ERROR", "Invalid request: timestamp is in the future.")
    return parsed


def _entry(row) -> dict:
    return {
        "id": row["id"],
        "timestamp": row["ts"],
        "core_temp_c": clean_number(row["core_temp_c"]),
        "unit": "°C",
        "method": row["method"],
        "note": row["note"],
        "temp_type": "core",
        "measurement_method": "manual",
        "data_label": config.DATA_LABEL,
    }


@router.post("/core-temperature", status_code=201)
def add_core_temperature(body: CoreTemperatureBody, conn=Depends(get_db)):
    now = config.reference_now().replace(microsecond=0)
    measured = _measured_at(body.timestamp, now)
    cur = conn.execute(
        "INSERT INTO core_temperatures (astronaut_id, ts, core_temp_c, method, note, recorded_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (config.default_astronaut_id(), measured.strftime(TS_FORMAT), body.core_temp_c, body.method,
         (body.note or "").strip() or None, now.strftime(TS_FORMAT)),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM core_temperatures WHERE id = ?", (cur.lastrowid,)).fetchone()
    return {"entry": _entry(row), "disclaimer": DISCLAIMER}


@router.get("/core-temperature")
def list_core_temperature(limit: int = Query(50, ge=1, le=200), conn=Depends(get_db)):
    """The latest `limit` manual core-temperature entries, oldest first."""
    rows = conn.execute(
        "SELECT * FROM (SELECT * FROM core_temperatures WHERE astronaut_id = ? ORDER BY ts DESC, id DESC LIMIT ?) "
        "ORDER BY ts ASC, id ASC",
        (config.default_astronaut_id(), limit),
    ).fetchall()
    return {"data_label": config.DATA_LABEL, "entries": [_entry(r) for r in rows], "disclaimer": DISCLAIMER}
