"""One chronological pass over the readings: valid value, baseline, delta and a day-level flag
for every metric on every day. The rules then read this table.

A reading is "flagged" when its own day-level condition is met (for example heart rate 15 bpm
or more above baseline). Flagged readings are left out of later baselines.
"""
from __future__ import annotations

from app.engine import rules_config as rc
from app.engine.baseline import rolling_baseline
from app.engine.quality import valid_value

METRICS = ("heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c")
EPS = 1e-9


def is_flagged(metric, value, baseline, cfg):
    if value is None:
        return False
    if metric == "sleep_hours":
        # ASSUMPTION: a night is flagged when under the SLEEP-01 hours or SLEEP-02 below baseline
        if value < cfg["SLEEP-01"]["hours"]:
            return True
        return baseline is not None and value - baseline <= -cfg["SLEEP-02"]["below_baseline_hours"] + EPS
    if baseline is None:
        return False
    delta = value - baseline
    if metric == "heart_rate_bpm":
        return delta >= cfg["HR-01"]["delta_bpm"] - EPS
    if metric == "spo2_pct":
        return delta <= -cfg["SPO2-01"]["drop_points"] + EPS
    if metric == "body_temp_c":
        return delta >= cfg["TEMP-01"]["temp_delta_threshold"] - EPS
    return False


def analyze(series, cfg=None):
    """Returns one dict per row: {metric: {value, baseline, delta, flagged}}."""
    cfg = cfg or rc.RULES_CONFIG
    n = len(series)
    values = {m: [valid_value(r, m) for r in series] for m in METRICS}
    flagged = {m: [False] * n for m in METRICS}
    days = []
    for i in range(n):
        day = {}
        for m in METRICS:
            v = values[m][i]
            b = rolling_baseline(series, values[m], flagged[m], i, m)
            if b is None and m in rc.PREFLIGHT_BASELINE:
                b = rc.PREFLIGHT_BASELINE[m]
            flagged[m][i] = is_flagged(m, v, b, cfg)
            day[m] = {
                "value": v,
                "baseline": b,
                "delta": None if v is None or b is None else v - b,
                "flagged": flagged[m][i],
            }
        days.append(day)
    return days
