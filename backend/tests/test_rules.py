from app.engine import rules
from app.engine.rules_config import RULES_CONFIG
from tests.helpers import ids, make_series, ts


def only(rule_id, alerts):
    found = [a for a in alerts if a["rule_id"] == rule_id]
    return found[0] if found else None


def last_day(**cols):
    n = len(next(iter(cols.values())))
    return rules.evaluate(make_series(n, **cols))


# ------------------------------------------------------------ HR-01
def test_hr01_normal_and_borderline_do_not_fire():
    assert only("HR-01", last_day(heart_rate_bpm=[60] * 7 + [62])) is None
    assert only("HR-01", last_day(heart_rate_bpm=[60] * 7 + [74])) is None


def test_hr01_fires_at_15_above_baseline_with_ammara_fields():
    a = only("HR-01", last_day(heart_rate_bpm=[60] * 7 + [75]))
    assert a["rule"] == "Resting heart rate above personal baseline"
    assert (a["severity"], a["category"], a["unit"]) == ("watch", "physiological", "bpm")
    assert (a["value"], a["baseline"], a["delta"]) == (75, 60, 15)
    assert a["baseline_status"] == "established" and a["data_quality"] == "good"
    assert a["source"] == "Prototype rule (context: S2, S4)"
    assert a["message"] == ("Resting heart rate is 75 bpm, 15 bpm above this astronaut's 7-day baseline of 60 bpm.")
    assert a["next_step"].startswith("Repeat at rest under the same conditions")


def test_hr01_needs_an_established_baseline():
    assert only("HR-01", last_day(heart_rate_bpm=[60] * 6 + [90])) is None


def test_hr01_ignores_a_poor_quality_reading():
    s = make_series(8, heart_rate_bpm=[60] * 7 + [90], hr_quality=["good"] * 7 + ["poor"])
    assert only("HR-01", rules.evaluate(s)) is None


# ------------------------------------------------------------ HR-02
def test_hr02_needs_two_consecutive_days():
    assert only("HR-02", last_day(heart_rate_bpm=[60] * 7 + [75, 60])) is None
    a = only("HR-02", last_day(heart_rate_bpm=[60] * 7 + [75, 76]))
    assert a["severity"] == "attention" and a["rule"] == "Persistent heart rate deviation"


# ------------------------------------------------------------ SPO2-01
def test_spo2_relative_not_absolute():
    # 93 is a low absolute value but only 1 point below this astronaut's baseline of 94: no alert
    assert only("SPO2-01", last_day(spo2_pct=[94] * 7 + [93, 93])) is None


def test_spo2_needs_three_points_on_two_consecutive_valid_readings():
    assert only("SPO2-01", last_day(spo2_pct=[97] * 7 + [94])) is None                 # one reading only
    assert only("SPO2-01", last_day(spo2_pct=[97] * 7 + [95, 94])) is None             # 95 is only 2 below
    a = only("SPO2-01", last_day(spo2_pct=[97] * 7 + [94, 94]))
    assert a["severity"] == "watch" and a["unit"] == "%" and a["delta"] == -3


def test_spo2_poor_quality_reading_is_a_data_problem_not_an_alert():
    s = make_series(9, spo2_pct=[97] * 7 + [94, 94], spo2_quality=["good"] * 7 + ["poor", "good"])
    alerts = rules.evaluate(s)
    assert only("SPO2-01", alerts) is None            # previous valid reading (day 7) was normal
    s2 = make_series(8, spo2_pct=[97] * 7 + [80], spo2_quality=["good"] * 7 + ["poor"])
    assert "DATA-01" in ids(rules.evaluate(s2)) and "SPO2-01" not in ids(rules.evaluate(s2))


# ------------------------------------------------------------ SLEEP-01 / SLEEP-02
def test_sleep01_fires_after_three_nights_under_six():
    a = only("SLEEP-01", last_day(sleep_hours=[7, 7, 7, 7, 7, 7, 7, 5.9, 5.8, 5.5]))
    assert a["rule"] == "Sleep under 6 hours for 3 nights" and a["severity"] == "notice"
    assert a["source"] == "Team guide rule (context: S7)"


def test_sleep01_borderline_and_two_nights_do_not_fire():
    assert only("SLEEP-01", last_day(sleep_hours=[7] * 7 + [5.9, 6.0, 5.5])) is None
    assert only("SLEEP-01", last_day(sleep_hours=[7] * 8 + [5.9, 5.5])) is None


def test_sleep01_does_not_need_a_baseline():
    a = only("SLEEP-01", last_day(sleep_hours=[5.9, 5.8, 5.5]))
    assert a is not None and a["baseline"] is None and a["baseline_status"] == "not_established"


def test_sleep02_needs_three_nights_at_least_1_5_below_baseline():
    a = only("SLEEP-02", last_day(sleep_hours=[8.0] * 7 + [6.4, 6.4, 6.4]))   # 1.6 below, not under 6
    assert a["severity"] == "watch" and a["rule"] == "Sleep below personal baseline"
    assert only("SLEEP-01", last_day(sleep_hours=[8.0] * 7 + [6.4, 6.4, 6.4])) is None
    assert only("SLEEP-02", last_day(sleep_hours=[8.0] * 7 + [6.6, 6.6, 6.6])) is None   # only 1.4 below
    assert only("SLEEP-02", last_day(sleep_hours=[8.0] * 7 + [6.4, 6.4])) is None         # two nights


# ------------------------------------------------------------ TEMP-01
def test_temp01_needs_two_consecutive_comparable_readings():
    assert only("TEMP-01", last_day(body_temp_c=[33.5] * 7 + [34.5])) is None            # single spike
    assert only("TEMP-01", last_day(body_temp_c=[33.5] * 7 + [33.9, 33.9])) is None      # only +0.4
    a = only("TEMP-01", last_day(body_temp_c=[33.5] * 7 + [34.0, 34.0]))
    assert a["severity"] == "watch" and a["temp_type"] == "skin" and a["unit"] == "°C"
    assert a["sensor_location"] == "wrist" and a["device"] == "wearable-01"
    assert a["measurement_method"] == "wearable" and "not core temperature" in a["message"]


def test_temp01_ignores_invalid_readings():
    s = make_series(9, body_temp_c=[33.5] * 7 + [34.0, 34.0], temp_contact_quality=["good"] * 8 + ["poor"])
    assert only("TEMP-01", rules.evaluate(s)) is None


def test_temp01_threshold_is_configurable():
    cfg = {k: dict(v) for k, v in RULES_CONFIG.items()}
    cfg["TEMP-01"]["temp_delta_threshold"] = 0.8
    s = make_series(9, body_temp_c=[33.5] * 7 + [34.0, 34.0])
    assert only("TEMP-01", rules.evaluate(s, config=cfg)) is None


def test_physiological_alerts_other_than_temp_have_no_temperature_fields():
    a = only("HR-01", last_day(heart_rate_bpm=[60] * 7 + [75]))
    assert (a["temp_type"], a["sensor_location"], a["device"], a["measurement_method"]) == (None,) * 4


# ------------------------------------------------------------ DATA-01 / DATA-02
def test_data01_poor_quality_and_missing():
    a = only("DATA-01", rules.evaluate(make_series(9, spo2_quality=["good"] * 8 + ["poor"])))
    assert a["severity"] == "notice" and a["category"] == "data_quality" and a["data_quality"] == "poor"
    assert a["rule"] == "Insufficient or unreliable data" and a["value"] is None
    assert "No health event is inferred" in a["message"]
    m = only("DATA-01", rules.evaluate(make_series(9, heart_rate_bpm=[62] * 8 + [None])))
    assert m["data_quality"] == "insufficient"


def test_data01_gap_between_readings():
    stamps = [ts(i) for i in range(8)] + [ts(11)]       # three missing days
    assert only("DATA-01", rules.evaluate(make_series(9, timestamp=stamps))) is not None


def test_data01_clean_day_has_no_data_alert():
    assert only("DATA-01", last_day(heart_rate_bpm=[62] * 10)) is None


def test_data02_baseline_not_established_and_no_personalised_alerts():
    alerts = rules.evaluate(make_series(5, heart_rate_bpm=[60, 60, 60, 60, 90]))
    d = only("DATA-02", alerts)
    assert d["severity"] == "notice" and d["category"] == "setup" and d["baseline"] is None
    assert d["baseline_status"] == "not_established"
    assert not {"HR-01", "HR-02", "SPO2-01", "SLEEP-02", "TEMP-01"} & set(ids(alerts))


def test_data02_goes_away_once_a_baseline_exists():
    assert only("DATA-02", last_day(heart_rate_bpm=[62] * 8)) is None


# ------------------------------------------------------------ ordering, ids, switches
def test_most_severe_first_and_ids_follow_that_order():
    alerts = last_day(heart_rate_bpm=[60] * 7 + [75, 76], sleep_hours=[7.0] * 7 + [5.5, 5.5])
    assert alerts[0]["rule_id"] == "HR-02" and alerts[0]["id"] == "a1"
    assert [a["id"] for a in alerts] == [f"a{i}" for i in range(1, len(alerts) + 1)]
    sev = [a["severity"] for a in alerts]
    assert sev == sorted(sev, key=lambda s: -{"notice": 1, "watch": 2, "attention": 3}[s])


def test_normal_period_has_no_alerts():
    # a clean period only raises DATA-02 during the 7 day calibration window, then nothing
    assert ids(rules.evaluate_all(make_series(12))) == ["DATA-02"] * 7


def test_disabled_rule_is_skipped():
    cfg = {k: dict(v) for k, v in RULES_CONFIG.items()}
    cfg["HR-01"]["enabled"] = False
    assert only("HR-01", rules.evaluate(make_series(8, heart_rate_bpm=[60] * 7 + [90]), config=cfg)) is None


def test_every_alert_has_all_fields_ammara_asked_for():
    a = last_day(heart_rate_bpm=[60] * 7 + [75])[0]
    for key in ("rule_id", "rule", "severity", "category", "metric", "value", "unit", "baseline", "delta",
                "baseline_status", "timestamp", "message", "next_step", "source", "data_quality",
                "temp_type", "sensor_location", "device", "measurement_method"):
        assert key in a
