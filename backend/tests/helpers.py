from datetime import datetime, timedelta, timezone

DEFAULTS = {"heart_rate_bpm": 62, "spo2_pct": 97, "sleep_hours": 7.0, "body_temp_c": 36.6}


def make_series(n=10, **overrides):
    """Build n daily readings. Pass metric=[list of n values] to override a metric."""
    base = datetime(2026, 11, 1, 8, tzinfo=timezone.utc)
    rows = []
    for i in range(n):
        row = {"timestamp": (base + timedelta(days=i)).strftime("%Y-%m-%dT%H:%M:%SZ")}
        for metric, default in DEFAULTS.items():
            row[metric] = overrides.get(metric, [default] * n)[i]
        rows.append(row)
    return rows
