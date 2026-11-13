from app.engine import rules
from app.engine.rules_config import RULES_CONFIG
from tests.helpers import make_series


def fire(rule_id, series):
    fn = dict(rules.RULE_FUNCS)[rule_id]
    return fn(series, len(series) - 1, RULES_CONFIG[rule_id])


# ---- hr_above_baseline ----
def test_hr_normal_no_alert():
    assert fire("hr_above_baseline", make_series(8, heart_rate_bpm=[60] * 7 + [62])) is None


def test_hr_borderline_no_alert():
    assert fire("hr_above_baseline", make_series(8, heart_rate_bpm=[60] * 7 + [74])) is None


def test_hr_abnormal_alert():
    a = fire("hr_above_baseline", make_series(8, heart_rate_bpm=[60] * 7 + [75]))
    assert a and a["severity"] == "watch" and a["value"] == 75 and a["baseline"] == 60
    assert a["message"] == "Heart rate is 15 bpm above your 7-day baseline."


def test_hr_skipped_without_baseline():
    assert fire("hr_above_baseline", make_series(2, heart_rate_bpm=[60, 90])) is None


# ---- sleep_low_streak ----
def test_sleep_abnormal_alert():
    a = fire("sleep_low_streak", make_series(5, sleep_hours=[7, 7, 5.9, 5.8, 5.5]))
    assert a and a["severity"] == "notice"
    assert a["rule"] == "Sleep under 6 hours for 3 nights in a row"


def test_sleep_borderline_exactly_six_no_alert():
    assert fire("sleep_low_streak", make_series(5, sleep_hours=[7, 7, 5.9, 6.0, 5.5])) is None


def test_sleep_two_nights_only_no_alert():
    assert fire("sleep_low_streak", make_series(5, sleep_hours=[7, 7, 7, 5.9, 5.5])) is None


# ---- spo2_low ----
def test_spo2_tiers():
    assert fire("spo2_low", make_series(5, spo2_pct=[97, 97, 97, 97, 94])) is None
    assert fire("spo2_low", make_series(5, spo2_pct=[97, 97, 97, 97, 93]))["severity"] == "watch"
    assert fire("spo2_low", make_series(5, spo2_pct=[97, 97, 97, 97, 89]))["severity"] == "attention"


# ---- temp_high ----
def test_temp_tiers():
    assert fire("temp_high", make_series(5, body_temp_c=[36.6] * 4 + [37.7])) is None
    assert fire("temp_high", make_series(5, body_temp_c=[36.6] * 4 + [37.8]))["severity"] == "watch"
    assert fire("temp_high", make_series(5, body_temp_c=[36.6] * 4 + [38.0]))["severity"] == "attention"


# ---- hr_absolute_high ----
def test_hr_absolute():
    assert fire("hr_absolute_high", make_series(5, heart_rate_bpm=[62] * 4 + [100])) is None
    assert fire("hr_absolute_high", make_series(5, heart_rate_bpm=[62] * 4 + [101]))["severity"] == "attention"


# ---- evaluate() ----
def test_evaluate_sorts_most_severe_first_and_assigns_ids():
    s = make_series(8, heart_rate_bpm=[60] * 7 + [110], sleep_hours=[7, 7, 7, 7, 5.5, 5.5, 5.5, 5.5])
    alerts = rules.evaluate(s)
    assert [a["id"] for a in alerts] == [f"a{i}" for i in range(1, len(alerts) + 1)]
    assert alerts[0]["severity"] == "attention"
    assert alerts[-1]["severity"] == "notice"


def test_evaluate_normal_day_has_no_alerts():
    assert rules.evaluate(make_series(10)) == []


def test_disabled_rule_is_skipped():
    cfg = {k: dict(v) for k, v in RULES_CONFIG.items()}
    cfg["hr_above_baseline"]["enabled"] = False
    s = make_series(8, heart_rate_bpm=[60] * 7 + [90])
    ids = [a["rule_id"] for a in rules.evaluate(s, config=cfg)]
    assert "hr_above_baseline" not in ids
