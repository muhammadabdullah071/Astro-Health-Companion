"""Data-quality behaviour against the CURRENT engine (app/engine/quality.py + DATA-01).

This file previously imported a `plausible()` helper that existed only in an earlier
local experiment; the team's engine decides validity in `engine/quality.py` instead,
so these tests exercise that real implementation and the DATA-01 notice it feeds.

Deliberately NOT tested here: unit-level validity flags (already covered by
tests/test_quality.py), baseline exclusion of poor readings (tests/test_baseline.py)
and the demo data-quality scenario (tests/test_demo_scenario.py). This file covers
the integration points those files leave out.
"""
from __future__ import annotations

import pytest

from app.db import seed
from app.engine import rules
from app.engine.quality import reading_issue
from tests.helpers import make_series


def rule_ids(series):
    return [a["rule_id"] for a in rules.evaluate(series)]


# --------------------------------------------------------------------- vocabulary
@pytest.mark.parametrize("metric", ["heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c"])
def test_issue_vocabulary_stays_within_the_documented_values(metric):
    """DATA-01 wording and any UI mapping branch on these values.

    Only None (usable), "missing" and "poor_quality" are documented by Ammara's
    Section 2, so a new value must be a deliberate, reviewed change.
    """
    rows = [
        make_series(1)[0],
        make_series(1, **{metric: [None]})[0],
        make_series(1, body_temp_c=[50.0])[0],
    ]
    for row in rows:
        assert reading_issue(row, metric) in (None, "missing", "poor_quality")


# ------------------------------------- invalid readings become notices, not alerts
def test_poor_quality_heart_rate_spike_is_a_data_notice_only():
    """A bad sensor value must never look like a health event (spec HR-01 / DATA-01)."""
    series = make_series(
        9,
        heart_rate_bpm=[62] * 8 + [150],
        hr_quality=["good"] * 8 + ["poor"],
    )
    ids = rule_ids(series)
    assert "DATA-01" in ids
    assert "HR-01" not in ids and "HR-02" not in ids


def test_implausible_skin_temperature_is_excluded_and_reported_as_poor_quality():
    """45 °C is outside the 28-38 °C skin screen, so it is stored but never used."""
    series = make_series(9, body_temp_c=[33.5] * 8 + [45.0])
    alerts = rules.evaluate(series)
    ids = [a["rule_id"] for a in alerts]
    assert "TEMP-01" not in ids
    data = [a for a in alerts if a["rule_id"] == "DATA-01"]
    assert data, "an unusable skin reading must raise DATA-01, not be dropped silently"
    assert "skin temperature" in data[0]["message"].lower()
    assert data[0]["data_quality"] == "poor"


def test_missing_reading_is_reported_as_missing_not_as_a_physiological_alert():
    series = make_series(9, sleep_hours=[7.0] * 8 + [None])
    alerts = rules.evaluate(series)
    data = [a for a in alerts if a["rule_id"] == "DATA-01"]
    assert data and "missing" in data[0]["message"]
    assert data[0]["data_quality"] == "insufficient"
    assert "SLEEP-01" not in [a["rule_id"] for a in alerts]


# ------------------------------------------------------------- import boundary
def test_badly_formatted_value_is_rejected_at_import_time(tmp_path):
    """Bad formatting fails at the CSV boundary instead of reaching the rule engine."""
    bad = tmp_path / "bad.csv"
    bad.write_text(
        "timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c\n"
        "2026-11-01T08:00:00Z,not-a-number,97,7.0,33.5\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        seed.load_rows(bad)


# ---------------------------------------------------------------- known gap
def test_stale_timestamps_do_not_raise_data_01_known_gap():
    """KNOWN GAP (DATA-01, spec: "missing, stale, badly formatted, or poor-quality").

    The engine checks the gap *between* readings (DATA-01 gap_hours = 36) but never
    how old the newest reading is, so a dataset that stopped a year ago produces no
    notice. This test records the current behaviour so the gap is visible; if
    staleness detection is added it will fail and the assertion must be updated.
    """
    year_old = [row["timestamp"].replace("2026", "2025") for row in make_series(9)]
    series = make_series(9, timestamp=year_old, heart_rate_bpm=[62] * 9)
    assert "DATA-01" not in rule_ids(series)
