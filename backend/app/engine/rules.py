"""Ammara's eight transparent rules, one small function each.

A rule returns an alert dict or None. Every alert states the rule, value, unit, baseline,
difference, severity and time, so nothing is a black box.
"""
from __future__ import annotations

from app.engine import quality
from app.engine import rules_config as rc
from app.engine.analysis import METRICS, analyze
from app.engine.baseline import comparable, gap_hours

rc.validate_config()

UNITS = {"heart_rate_bpm": "bpm", "spo2_pct": "%", "sleep_hours": "hours", "body_temp_c": "°C"}
LABELS = {
    "heart_rate_bpm": "resting heart rate",
    "spo2_pct": "SpO2",
    "sleep_hours": "sleep",
    "body_temp_c": "skin temperature",
}


def _round(x):
    return None if x is None else round(x, 1)


def _alert(rule_id, cfg, series, i, metric, value, baseline, message, data_quality="good", skin_temp=False):
    row = series[i]
    delta = None if value is None or baseline is None else value - baseline
    alert = {
        "rule_id": rule_id,
        "rule": cfg["name"],
        "severity": cfg["severity"],
        "category": cfg["category"],
        "metric": metric,
        "value": _round(value),
        "unit": UNITS.get(metric),
        "baseline": _round(baseline),
        "delta": _round(delta),
        "baseline_status": "established" if baseline is not None else "not_established",
        "timestamp": row["timestamp"],
        "message": message,
        "next_step": cfg["next_step"],
        "source": cfg["source"],
        "data_quality": data_quality,
        "temp_type": None,
        "sensor_location": None,
        "device": None,
        "measurement_method": None,
    }
    if skin_temp:
        alert.update(
            temp_type="skin",
            sensor_location=quality.get(row, "temp_sensor_location"),
            device=quality.get(row, "temp_device_id"),
            measurement_method="wearable",
        )
    return alert


def _previous_valid(analysis, i, metric):
    for j in range(i - 1, -1, -1):
        if analysis[j][metric]["value"] is not None:
            return j
    return None


# ---------------------------------------------------------------- physiological rules
def hr_01(series, analysis, i, cfg):
    d = analysis[i]["heart_rate_bpm"]
    if not d["flagged"]:
        return None
    msg = (f"Resting heart rate is {d['value']:.0f} bpm, {d['delta']:.0f} bpm above this astronaut's "
           f"{rc.BASELINE_DAYS}-day baseline of {d['baseline']:.0f} bpm.")
    return _alert("HR-01", cfg, series, i, "heart_rate_bpm", d["value"], d["baseline"], msg)


def hr_02(series, analysis, i, cfg):
    d = analysis[i]["heart_rate_bpm"]
    if not d["flagged"] or i == 0 or not analysis[i - 1]["heart_rate_bpm"]["flagged"]:
        return None
    limit = rc.RULES_CONFIG["HR-01"]["delta_bpm"]
    msg = (f"Resting heart rate has been {limit} bpm or more above this astronaut's baseline on 2 consecutive "
           f"daily readings (latest {d['value']:.0f} bpm against a baseline of {d['baseline']:.0f} bpm).")
    return _alert("HR-02", cfg, series, i, "heart_rate_bpm", d["value"], d["baseline"], msg)


def spo2_01(series, analysis, i, cfg):
    d = analysis[i]["spo2_pct"]
    if not d["flagged"]:
        return None
    j = _previous_valid(analysis, i, "spo2_pct")
    if j is None or not analysis[j]["spo2_pct"]["flagged"]:
        return None
    msg = (f"SpO2 is {d['value']:.0f}%, {abs(d['delta']):.0f} percentage points below this astronaut's "
           f"baseline of {d['baseline']:.0f}% on 2 consecutive valid readings.")
    return _alert("SPO2-01", cfg, series, i, "spo2_pct", d["value"], d["baseline"], msg)


def sleep_01(series, analysis, i, cfg):
    nights = cfg["nights"]
    if i + 1 < nights:
        return None
    for j in range(i - nights + 1, i + 1):
        v = analysis[j]["sleep_hours"]["value"]
        if v is None or not v < cfg["hours"]:
            return None
    d = analysis[i]["sleep_hours"]
    msg = (f"Sleep has been under {cfg['hours']:g} hours for {nights} nights in a row "
           f"(latest night {d['value']:g} hours).")
    return _alert("SLEEP-01", cfg, series, i, "sleep_hours", d["value"], d["baseline"], msg)


def sleep_02(series, analysis, i, cfg):
    nights, limit = cfg["nights"], cfg["below_baseline_hours"]
    if i + 1 < nights:
        return None
    for j in range(i - nights + 1, i + 1):
        d = analysis[j]["sleep_hours"]
        if d["value"] is None or d["baseline"] is None or d["value"] - d["baseline"] > -limit + 1e-9:
            return None
    d = analysis[i]["sleep_hours"]
    msg = (f"Sleep is {abs(d['delta']):.1f} hours below this astronaut's {rc.BASELINE_DAYS}-night baseline of "
           f"{d['baseline']:.1f} hours, and has been at least {limit:g} hours below it for {nights} consecutive nights.")
    return _alert("SLEEP-02", cfg, series, i, "sleep_hours", d["value"], d["baseline"], msg)


def temp_01(series, analysis, i, cfg):
    d = analysis[i]["body_temp_c"]
    if not d["flagged"]:
        return None
    # previous comparable reading: same time window and same sensor location
    j = next((k for k in range(i - 1, -1, -1)
              if analysis[k]["body_temp_c"]["value"] is not None and comparable(series, k, i, "body_temp_c")), None)
    if j is None or not analysis[j]["body_temp_c"]["flagged"]:
        return None
    if gap_hours(series[j], series[i]) < cfg["min_gap_hours"]:
        return None
    msg = (f"Skin temperature is {d['value']:.1f} °C, {d['delta']:.1f} °C above this astronaut's skin baseline of "
           f"{d['baseline']:.1f} °C on 2 consecutive comparable readings. This is a skin reading, not core temperature.")
    return _alert("TEMP-01", cfg, series, i, "body_temp_c", d["value"], d["baseline"], msg, skin_temp=True)


# ---------------------------------------------------------------- data rules
def data_01(series, analysis, i, cfg):
    row = series[i]
    problems, affected, poor = [], [], False
    for m in METRICS:
        issue = quality.reading_issue(row, m)
        if issue:
            affected.append(m)
            poor = poor or issue == "poor_quality"
            problems.append(f"{LABELS[m]} ({'missing' if issue == 'missing' else 'poor quality'})")
    if i > 0 and gap_hours(series[i - 1], row) > cfg["gap_hours"]:
        problems.append("missing readings since the previous entry")
    if not problems:
        return None
    metric = affected[0] if affected else "data"
    baseline = analysis[i][metric]["baseline"] if affected else None
    msg = "Insufficient or unreliable data: " + ", ".join(problems) + ". No health event is inferred."
    return _alert("DATA-01", cfg, series, i, metric, None, baseline, msg,
                  data_quality="poor" if poor else "insufficient")


def data_02(series, analysis, i, cfg):
    missing = [m for m in METRICS
               if analysis[i][m]["value"] is not None and analysis[i][m]["baseline"] is None]
    if not missing:
        return None
    labels = ", ".join(LABELS[m] for m in missing)
    msg = (f"Baseline not established for {labels}: fewer than {rc.BASELINE_MIN_DAYS} days of usable comparable "
           f"data and no approved preflight baseline. Personalised deviation alerts are paused; raw trends are still shown.")
    first = missing[0]
    return _alert("DATA-02", cfg, series, i, first, analysis[i][first]["value"], None, msg,
                  data_quality="insufficient")


RULE_FUNCS = [
    ("HR-01", hr_01),
    ("HR-02", hr_02),
    ("SPO2-01", spo2_01),
    ("SLEEP-01", sleep_01),
    ("SLEEP-02", sleep_02),
    ("TEMP-01", temp_01),
    ("DATA-01", data_01),
    ("DATA-02", data_02),
]


def _run(series, analysis, i, cfg_all):
    found = []
    for order, (rule_id, fn) in enumerate(RULE_FUNCS):
        cfg = cfg_all.get(rule_id)
        if not cfg or not cfg.get("enabled", True):
            continue
        alert = fn(series, analysis, i, cfg)
        if alert:
            found.append((order, alert))
    return found


def _sort_and_number(found):
    """Most severe first, then newest first, then rule order. Ids are a1, a2, ... in that order."""
    found.sort(key=lambda t: t[0])
    found.sort(key=lambda t: t[1]["timestamp"], reverse=True)
    found.sort(key=lambda t: -rc.SEVERITY_RANK[t[1]["severity"]])
    alerts = []
    for position, (_, alert) in enumerate(found, start=1):
        alert["id"] = f"a{position}"
        alert["position"] = position
        alerts.append(alert)
    return alerts


def evaluate(series, idx=None, config=None):
    """Alerts for one day (default: the latest reading)."""
    if not series:
        return []
    cfg_all = config or rc.RULES_CONFIG
    idx = len(series) - 1 if idx is None else idx
    analysis = analyze(series, cfg_all)
    return _sort_and_number(_run(series, analysis, idx, cfg_all))


def evaluate_all(series, config=None):
    """Alerts for EVERY day, so charts can show markers (day 20 and days 24 to 26 in the demo)."""
    cfg_all = config or rc.RULES_CONFIG
    analysis = analyze(series, cfg_all)
    found = []
    for i in range(len(series)):
        found.extend(_run(series, analysis, i, cfg_all))
    return _sort_and_number(found)
