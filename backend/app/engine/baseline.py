"""Personal baseline helpers. Pure functions: no database, easy to test.

Baseline policy (Ammara, Section 2): the mean of 7 valid readings, excluding readings that
triggered an alert, so an active alert is never silently normalised. Fewer than 7 usable
readings means "baseline not established" (the function returns None).
"""
from __future__ import annotations

from app.engine import quality
from app.engine import rules_config as rc
from app.utils import parse_ts


def time_window(ts):
    """overnight, morning, afternoon or evening, from the UTC hour of the timestamp."""
    hour = parse_ts(ts).hour
    for name, (low, high) in rc.TIME_WINDOWS.items():
        if low <= hour < high:
            return name
    return "overnight"


def gap_hours(earlier_row, later_row):
    return (parse_ts(later_row["timestamp"]) - parse_ts(earlier_row["timestamp"])).total_seconds() / 3600


def comparable(series, j, i, metric):
    """Skin temperature is only comparable in the same time window and from the same sensor location."""
    if metric != "body_temp_c":
        return True
    a, b = series[j], series[i]
    return (
        time_window(a["timestamp"]) == time_window(b["timestamp"])
        and quality.get(a, "temp_sensor_location") == quality.get(b, "temp_sensor_location")
    )


def rolling_baseline(series, values, flagged, i, metric):
    """Baseline for row i, or None when it is not established.

    values:  per row, the valid reading or None
    flagged: per row, True when that reading already triggered a day-level alert
    ASSUMPTION (to confirm with Ammara): take the last 7 valid, non-flagged, comparable readings
    found within the previous BASELINE_LOOKBACK_ROWS rows.
    """
    start = max(0, i - rc.BASELINE_LOOKBACK_ROWS)
    candidates = [
        j for j in range(start, i)
        if values[j] is not None and not flagged[j] and comparable(series, j, i, metric)
    ]
    candidates = candidates[-rc.BASELINE_DAYS:]
    if len(candidates) < rc.BASELINE_MIN_DAYS:
        return None
    return sum(values[j] for j in candidates) / len(candidates)


def trend_slope(values):
    """Least-squares slope per step (per day). Positive means rising."""
    pts = [(i, v) for i, v in enumerate(values) if v is not None]
    n = len(pts)
    if n < 2:
        return 0.0
    mx = sum(i for i, _ in pts) / n
    my = sum(v for _, v in pts) / n
    den = sum((i - mx) ** 2 for i, _ in pts)
    if den == 0:
        return 0.0
    return sum((i - mx) * (v - my) for i, v in pts) / den
