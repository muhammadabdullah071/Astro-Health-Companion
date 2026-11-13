"""All alert thresholds in ONE place.

EVERY NUMBER HERE IS A PLACEHOLDER (common general-health values) until Ammara
confirms the indicator list and thresholds with Sofia. Change numbers here only;
the rule code in rules.py does not need to change.
"""
from __future__ import annotations

BASELINE_WINDOW_DAYS = 7   # personal baseline = mean of the previous N days
BASELINE_MIN_DAYS = 3      # with fewer days than this, baseline rules are skipped

SEVERITY_RANK = {"notice": 1, "watch": 2, "attention": 3}

PLACEHOLDER_SOURCE = "PLACEHOLDER: source to be added by Ammara"

RULES_CONFIG = {
    "hr_above_baseline": {
        "enabled": True,
        "name": "Resting heart rate above personal baseline",
        "delta_bpm": 15,
        "severity": "watch",
        "next_step": "Rest, re-measure after 15 minutes, and log how you feel. Follow mission medical procedure if it stays high.",
        "source": PLACEHOLDER_SOURCE,
    },
    "sleep_low_streak": {
        "enabled": True,
        "hours": 6.0,
        "nights": 3,
        "severity": "notice",
        "next_step": "Protect the next sleep period and review workload and light exposure.",
        "source": PLACEHOLDER_SOURCE,
    },
    "spo2_low": {
        "enabled": True,
        "name": "Oxygen saturation below limit",
        "watch_below": 94,
        "attention_below": 90,
        "next_step": "Re-measure with the sensor correctly placed. Follow mission medical procedure if it stays low.",
        "source": PLACEHOLDER_SOURCE,
    },
    "temp_high": {
        "enabled": True,
        "name": "Body temperature above limit",
        "watch_at_or_above": 37.8,
        "attention_at_or_above": 38.0,
        "next_step": "Re-measure after resting, hydrate, and follow mission medical procedure.",
        "source": PLACEHOLDER_SOURCE,
    },
    "hr_absolute_high": {
        "enabled": True,
        "name": "Resting heart rate above absolute limit",
        "above_bpm": 100,
        "severity": "attention",
        "next_step": "Rest, re-measure, and follow mission medical procedure.",
        "source": PLACEHOLDER_SOURCE,
    },
}
