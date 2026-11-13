"""Reading validity checks (Ammara, Section 2).

Invalid readings are stored but excluded from baselines and alerts, and they feed DATA-01.
"""
from __future__ import annotations

from app.engine import rules_config as rc

# Used when a reading has no quality information (for example Sofia's CSV has only the 5 core columns)
QUALITY_DEFAULTS = {
    "hr_quality": "good",
    "spo2_quality": "good",
    "sleep_source": "wearable",
    "temp_sensor_location": "wrist",
    "temp_device_id": "wearable-01",
    "temp_contact_quality": "good",
    "temp_dropout": 0,
}


def get(row, key):
    """Row value, or the default when the row has none."""
    value = row.get(key)
    return QUALITY_DEFAULTS.get(key) if value is None else value


def reading_issue(row, metric):
    """None when the reading is usable, otherwise 'missing' or 'poor_quality'."""
    value = row.get(metric)
    if value is None:
        return "missing"
    if metric == "heart_rate_bpm":
        ok = get(row, "hr_quality") == "good"
    elif metric == "spo2_pct":
        ok = get(row, "spo2_quality") == "good"
    elif metric == "sleep_hours":
        ok = bool(get(row, "sleep_source"))
    elif metric == "body_temp_c":
        low, high = rc.TEMP_VALID_RANGE_C
        ok = (
            bool(get(row, "temp_sensor_location"))
            and bool(get(row, "temp_device_id"))
            and get(row, "temp_contact_quality") == "good"
            and not get(row, "temp_dropout")
            and low <= float(value) <= high
        )
    else:
        ok = True
    return None if ok else "poor_quality"


def valid_value(row, metric):
    """The reading as a float, or None when it is missing or invalid."""
    return float(row[metric]) if reading_issue(row, metric) is None else None
