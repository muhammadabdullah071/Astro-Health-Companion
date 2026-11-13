from __future__ import annotations

from datetime import datetime, timezone


def clean_number(v):
    """78.0 -> 78 so JSON looks like the contract; other values unchanged."""
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def parse_ts(ts: str) -> datetime:
    """Parse an ISO UTC timestamp such as 2026-11-14T08:00:00Z."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
