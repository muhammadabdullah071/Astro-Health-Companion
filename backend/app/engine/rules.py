"""Plain, transparent alert rules. One small function per rule.

A rule returns an alert dict or None. Each alert states the rule, measured value,
baseline, severity and time, so nothing is a black box.
"""
from __future__ import annotations

from app.engine.baseline import consecutive_below, rolling_baseline
from app.engine.rules_config import BASELINE_WINDOW_DAYS, RULES_CONFIG, SEVERITY_RANK


def _val(series, idx, metric):
    v = series[idx].get(metric)
    return None if v is None else float(v)


def _alert(rule_id, cfg, name, severity, metric, value, baseline, ts, message):
    return {
        "rule_id": rule_id,
        "rule": name,
        "severity": severity,
        "metric": metric,
        "value": round(value, 1),
        "baseline": None if baseline is None else round(baseline, 1),
        "timestamp": ts,
        "message": message,
        "next_step": cfg.get("next_step"),
        "source": cfg.get("source"),
    }


def hr_above_baseline(series, idx, cfg):
    v = _val(series, idx, "heart_rate_bpm")
    b = rolling_baseline(series, idx, "heart_rate_bpm")
    if v is None or b is None:
        return None
    delta = v - b
    if delta >= cfg["delta_bpm"]:
        return _alert("hr_above_baseline", cfg, cfg["name"], cfg["severity"], "heart_rate_bpm", v, b,
                      series[idx]["timestamp"],
                      f"Heart rate is {delta:.0f} bpm above your {BASELINE_WINDOW_DAYS}-day baseline.")
    return None


def sleep_low_streak(series, idx, cfg):
    if consecutive_below(series, idx, "sleep_hours", cfg["hours"], cfg["nights"]):
        name = f"Sleep under {cfg['hours']:g} hours for {cfg['nights']} nights in a row"
        return _alert("sleep_low_streak", cfg, name, cfg["severity"], "sleep_hours",
                      _val(series, idx, "sleep_hours"), rolling_baseline(series, idx, "sleep_hours"),
                      series[idx]["timestamp"],
                      f"Sleep has been under {cfg['hours']:g} hours for {cfg['nights']} nights in a row.")
    return None


def spo2_low(series, idx, cfg):
    v = _val(series, idx, "spo2_pct")
    if v is None:
        return None
    if v < cfg["attention_below"]:
        sev, limit = "attention", cfg["attention_below"]
    elif v < cfg["watch_below"]:
        sev, limit = "watch", cfg["watch_below"]
    else:
        return None
    return _alert("spo2_low", cfg, cfg["name"], sev, "spo2_pct", v, rolling_baseline(series, idx, "spo2_pct"),
                  series[idx]["timestamp"], f"Oxygen saturation is {v:.0f}%, below the {limit}% limit.")


def temp_high(series, idx, cfg):
    v = _val(series, idx, "body_temp_c")
    if v is None:
        return None
    if v >= cfg["attention_at_or_above"]:
        sev, limit = "attention", cfg["attention_at_or_above"]
    elif v >= cfg["watch_at_or_above"]:
        sev, limit = "watch", cfg["watch_at_or_above"]
    else:
        return None
    return _alert("temp_high", cfg, cfg["name"], sev, "body_temp_c", v, rolling_baseline(series, idx, "body_temp_c"),
                  series[idx]["timestamp"], f"Body temperature is {v:.1f} C, at or above the {limit:.1f} C limit.")


def hr_absolute_high(series, idx, cfg):
    v = _val(series, idx, "heart_rate_bpm")
    if v is None or not v > cfg["above_bpm"]:
        return None
    return _alert("hr_absolute_high", cfg, cfg["name"], cfg["severity"], "heart_rate_bpm", v,
                  rolling_baseline(series, idx, "heart_rate_bpm"), series[idx]["timestamp"],
                  f"Heart rate is {v:.0f} bpm, above the {cfg['above_bpm']} bpm limit.")


# Evaluation order (also the tie-break order for equal severity)
RULE_FUNCS = [
    ("hr_above_baseline", hr_above_baseline),
    ("sleep_low_streak", sleep_low_streak),
    ("spo2_low", spo2_low),
    ("temp_high", temp_high),
    ("hr_absolute_high", hr_absolute_high),
]


def evaluate(series, idx=None, config=None):
    """Run every enabled rule at position idx (default: latest reading).

    Returns alerts sorted most severe first, with ids a1, a2, ... assigned in that order.
    """
    if not series:
        return []
    idx = len(series) - 1 if idx is None else idx
    cfg_all = config or RULES_CONFIG
    found = []
    for order, (rule_id, fn) in enumerate(RULE_FUNCS):
        cfg = cfg_all.get(rule_id)
        if not cfg or not cfg.get("enabled", True):
            continue
        alert = fn(series, idx, cfg)
        if alert:
            found.append((order, alert))
    found.sort(key=lambda t: (-SEVERITY_RANK[t[1]["severity"]], t[0]))
    out = []
    for pos, (_, alert) in enumerate(found, start=1):
        alert["id"] = f"a{pos}"
        alert["position"] = pos
        out.append(alert)
    return out
