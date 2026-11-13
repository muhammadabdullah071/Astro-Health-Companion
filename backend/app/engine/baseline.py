"""Personal baseline and trend helpers. Pure functions: no database, easy to test."""
from __future__ import annotations

from app.engine.rules_config import BASELINE_MIN_DAYS, BASELINE_WINDOW_DAYS


def rolling_baseline(series, idx, metric, window=BASELINE_WINDOW_DAYS, min_days=BASELINE_MIN_DAYS):
    """Mean of the `window` days BEFORE position idx (the current day is excluded).

    Uses the days available when fewer than `window` exist; returns None when fewer
    than `min_days` values exist, so rules skip instead of guessing.
    """
    prev = [r[metric] for r in series[max(0, idx - window):idx] if r.get(metric) is not None]
    if len(prev) < min_days:
        return None
    return sum(prev) / len(prev)


def consecutive_below(series, idx, metric, threshold, nights):
    """True when the last `nights` values up to idx are all strictly below threshold."""
    if idx + 1 < nights:
        return False
    for j in range(idx - nights + 1, idx + 1):
        v = series[j].get(metric)
        if v is None or not v < threshold:
            return False
    return True


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
