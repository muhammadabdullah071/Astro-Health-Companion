"""Spec boundary cases for the eight rules that tests/test_rules.py does not cover.

tests/test_rules.py already covers the normal, borderline and triggered path of
every rule id on the current engine. This file adds only the remaining boundary
conditions from the deliverables spec: consecutiveness, missing readings,
TEMP-01 comparability and spacing, and the DATA-02 exit condition.

No rule threshold is redefined or changed here.
"""
from __future__ import annotations

from app.engine import rules
from app.engine import rules_config as rc
from tests.helpers import make_series, ts


def fired(series):
    return [a["rule_id"] for a in rules.evaluate(series)]


def alert(rule_id, series):
    found = [a for a in rules.evaluate(series) if a["rule_id"] == rule_id]
    return found[0] if found else None


# ---------------------------------------------------------------- HR-01 / HR-02
def test_hr01_missing_latest_reading_is_a_data_notice_only():
    ids = fired(make_series(9, heart_rate_bpm=[62] * 8 + [None]))
    assert "DATA-01" in ids
    assert "HR-01" not in ids and "HR-02" not in ids


def test_hr02_requires_consecutive_days_not_two_days_apart():
    # +15 bpm on day 8, normal on day 9, +17 bpm on day 10
    series = make_series(10, heart_rate_bpm=[60] * 7 + [75, 60, 77])
    ids = fired(series)
    assert "HR-01" in ids, "day 10 is still a single-day deviation"
    assert "HR-02" not in ids, "the two deviations are not consecutive"


def test_hr02_fires_when_both_days_are_exactly_fifteen_above_baseline():
    series = make_series(9, heart_rate_bpm=[60] * 7 + [75, 75])
    assert "HR-02" in fired(series)


# ------------------------------------------------------------------- SLEEP-01
def test_sleep01_does_not_fire_for_non_consecutive_short_nights():
    # self-control: three consecutive short nights do fire with the same values
    assert "SLEEP-01" in fired(make_series(9, sleep_hours=[7.0] * 6 + [5.4, 5.6, 5.2]))

    alternating = [5.5, 7.0] * 4 + [5.5]
    assert "SLEEP-01" not in fired(make_series(9, sleep_hours=alternating))


# ------------------------------------------------------------------- SLEEP-02
def test_sleep02_fires_at_exactly_one_and_a_half_hours_below_baseline():
    series = make_series(10, sleep_hours=[8.0] * 7 + [6.5, 6.5, 6.5])
    a = alert("SLEEP-02", series)
    assert a is not None
    assert a["delta"] == -1.5
    assert "SLEEP-01" not in fired(series), "6.5 h is not under 6 h"


def test_sleep02_needs_an_established_baseline():
    # self-control: the same three nights are judged once seven prior nights exist
    assert "SLEEP-02" in fired(make_series(10, sleep_hours=[8.0] * 7 + [6.5, 6.5, 6.5]))

    assert "SLEEP-02" not in fired(make_series(3, sleep_hours=[6.5, 6.5, 6.5]))


# -------------------------------------------------------------------- TEMP-01
def test_temp01_does_not_compare_different_time_windows():
    # self-control: the same pattern inside one morning window does fire
    assert "TEMP-01" in fired(make_series(9, body_temp_c=[33.5] * 7 + [34.1, 34.1]))

    stamps = [ts(day, 8) for day in range(8)] + [ts(8, 20)]
    series = make_series(9, timestamp=stamps, body_temp_c=[33.5] * 8 + [34.5])
    assert "TEMP-01" not in fired(series), "an evening reading has no comparable morning baseline"


def test_temp01_requires_at_least_four_hours_between_the_two_comparable_readings():
    # self-control: the same +0.5 °C pair one day apart does fire
    assert "TEMP-01" in fired(make_series(9, body_temp_c=[33.5] * 7 + [34.0, 34.0]))

    stamps = [ts(day, 8) for day in range(7)] + [ts(7, 8), ts(7, 10)]
    series = make_series(9, timestamp=stamps, body_temp_c=[33.5] * 7 + [34.0, 34.0])
    assert "TEMP-01" not in fired(series), "two readings 2 hours apart are not a sustained change"


def test_temp01_ignores_a_reading_from_a_different_sensor_location():
    # self-control: the same readings, all from the wrist, do fire
    assert "TEMP-01" in fired(make_series(9, body_temp_c=[33.5] * 7 + [34.1, 34.1]))

    series = make_series(
        9,
        body_temp_c=[33.5] * 7 + [34.1, 34.1],
        temp_sensor_location=["wrist"] * 8 + ["chest"],
    )
    assert "TEMP-01" not in fired(series)


def test_temp01_alert_states_it_is_skin_not_core_temperature():
    a = alert("TEMP-01", make_series(9, body_temp_c=[33.5] * 7 + [34.1, 34.1]))
    assert a is not None
    assert a["temp_type"] == "skin"
    assert "not core temperature" in a["message"]


# -------------------------------------------------------------------- DATA-02
def test_data02_stops_once_every_metric_has_seven_valid_readings():
    assert "DATA-02" not in fired(make_series(8))


# --------------------------------------------------------------- rule inventory
def test_engine_exposes_exactly_the_eight_spec_rules():
    """Guards the rule set so the QA coverage table cannot silently go stale."""
    engine_ids = [rule_id for rule_id, _ in rules.RULE_FUNCS]
    assert engine_ids == ["HR-01", "HR-02", "SPO2-01", "SLEEP-01", "SLEEP-02", "TEMP-01", "DATA-01", "DATA-02"]
    assert list(rc.RULES_CONFIG) == engine_ids
