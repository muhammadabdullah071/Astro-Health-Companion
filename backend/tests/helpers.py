from datetime import datetime, timedelta, timezone

DEFAULTS = {
    "heart_rate_bpm": 62,
    "spo2_pct": 97,
    "sleep_hours": 7.0,
    "body_temp_c": 33.5,
    "hr_quality": "good",
    "spo2_quality": "good",
    "sleep_source": "wearable",
    "temp_sensor_location": "wrist",
    "temp_device_id": "wearable-01",
    "temp_contact_quality": "good",
    "temp_dropout": 0,
}
START = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)


def ts(day, hour=8):
    return (START + timedelta(days=day)).replace(hour=hour).strftime("%Y-%m-%dT%H:%M:%SZ")


def make_series(n=10, **overrides):
    """n daily readings at 08:00. Pass column=[list of n values] to override a column,
    or timestamp=[...] to set your own timestamps."""
    rows = []
    for i in range(n):
        row = {"timestamp": overrides["timestamp"][i] if "timestamp" in overrides else ts(i)}
        for column, default in DEFAULTS.items():
            row[column] = overrides[column][i] if column in overrides else default
        rows.append(row)
    return rows


def ids(alerts):
    return [a["rule_id"] for a in alerts]
