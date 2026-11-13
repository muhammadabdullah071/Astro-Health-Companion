"""All rule settings in ONE place (Ammara's deliverables pack, 13 Nov 2026).

Rule ids, names, severities, next steps and sources come from her Section 3.
Every NUMBER is a prototype workflow rule, not a medical threshold. Change numbers here
only; the rule code in rules.py does not need to change.
"""
from __future__ import annotations

# ---- baseline policy (her Section 2) ----
BASELINE_DAYS = 7              # a baseline is the mean of 7 valid readings
BASELINE_MIN_DAYS = 7          # fewer than this: "Baseline not established" (DATA-02)
BASELINE_LOOKBACK_ROWS = 14    # ASSUMPTION: look back at most 14 readings to find those 7
PREFLIGHT_BASELINE: dict = {}  # optional approved preflight baseline, e.g. {"heart_rate_bpm": 62}
BASELINE_WINDOW_DAYS = BASELINE_DAYS  # old name, kept so older imports still work

# ---- skin temperature (her Section 2.1) ----
TIME_WINDOWS = {"overnight": (0, 6), "morning": (6, 12), "afternoon": (12, 18), "evening": (18, 24)}
TEMP_VALID_RANGE_C = (28.0, 38.0)   # proposed plausible physical range
TEMP_SENSOR_ACCURACY_C = 0.2        # PLACEHOLDER until the wearable is chosen
TEMP_NOISE_MARGIN_C = 0.1           # PLACEHOLDER until the wearable is chosen

SEVERITY_RANK = {"notice": 1, "watch": 2, "attention": 3}
RULE_ORDER = ["HR-01", "HR-02", "SPO2-01", "SLEEP-01", "SLEEP-02", "TEMP-01", "DATA-01", "DATA-02"]

RULES_CONFIG = {
    "HR-01": {
        "enabled": True,
        "name": "Resting heart rate above personal baseline",
        "severity": "watch",
        "category": "physiological",
        "delta_bpm": 15,
        "next_step": ("Repeat at rest under the same conditions; review recent sleep, exercise and symptoms; "
                      "follow the mission-approved protocol if it persists or symptoms appear"),
        "source": "Prototype rule (context: S2, S4)",
    },
    "HR-02": {
        "enabled": True,
        "name": "Persistent heart rate deviation",
        "severity": "attention",
        "category": "physiological",
        "next_step": ("Repeat the measurement; review trend and symptoms; "
                      "contact ground or medical officer per mission protocol"),
        "source": "Prototype rule (context: S3, S5)",
    },
    "SPO2-01": {
        "enabled": True,
        "name": "SpO2 below personal baseline",
        "severity": "watch",
        "category": "physiological",
        "drop_points": 3,
        "next_step": ("Repeat with good signal quality; check device fit and conditions; "
                      "review symptoms and protocol"),
        "source": "Prototype rule (context: S4)",
    },
    "SLEEP-01": {
        "enabled": True,
        "name": "Sleep under 6 hours for 3 nights",
        "severity": "notice",
        "category": "physiological",
        "hours": 6.0,
        "nights": 3,
        "next_step": ("Review schedule, workload, environment and fatigue; "
                      "consider approved sleep countermeasures"),
        "source": "Team guide rule (context: S7)",
    },
    "SLEEP-02": {
        "enabled": True,
        "name": "Sleep below personal baseline",
        "severity": "watch",
        "category": "physiological",
        "below_baseline_hours": 1.5,
        "nights": 3,
        "next_step": "Fatigue and mood check-in if available; schedule and rest review; monitor the trend",
        "source": "Prototype rule (context: S7)",
    },
    "TEMP-01": {
        "enabled": True,
        "name": "Skin temperature above personal baseline",
        "severity": "watch",
        "category": "physiological",
        "temp_delta_threshold": 0.5,   # configurable, provisional, pending sensor review
        "min_gap_hours": 4,            # proposed spacing for "sustained"
        "next_step": ("Repeat with the same site and method; check contact quality and conditions; "
                      "if it persists or symptoms appear, a manual core-temperature measurement may be "
                      "taken and entered per medical protocol"),
        "source": "Prototype rule (context: S4, S6)",
    },
    "DATA-01": {
        "enabled": True,
        "name": "Insufficient or unreliable data",
        "severity": "notice",
        "category": "data_quality",
        "gap_hours": 36,               # ASSUMPTION: a gap longer than this means missing readings
        "next_step": "Show 'insufficient data'; request a repeat or manual entry; infer no health event",
        "source": "Not a physiological alert",
    },
    "DATA-02": {
        "enabled": True,
        "name": "Baseline not established",
        "severity": "notice",
        "category": "setup",
        "next_step": "Keep collecting; show raw trends without personalised alerts",
        "source": "Prevents false precision",
    },
}


def validate_config(cfg=None) -> None:
    """The TEMP-01 threshold must not be lower than the sensor accuracy plus noise margin."""
    cfg = cfg or RULES_CONFIG
    floor = TEMP_SENSOR_ACCURACY_C + TEMP_NOISE_MARGIN_C
    if cfg["TEMP-01"]["temp_delta_threshold"] < floor:
        raise ValueError(
            f"temp_delta_threshold {cfg['TEMP-01']['temp_delta_threshold']} is below the sensor "
            f"accuracy plus noise margin ({floor})"
        )
