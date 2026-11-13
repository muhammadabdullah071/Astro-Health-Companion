from app.engine import rules_config
from app.engine.analysis import analyze
from app.engine.baseline import time_window, trend_slope
from tests.helpers import make_series, ts


def test_no_baseline_during_first_seven_days():
    a = analyze(make_series(8, heart_rate_bpm=[60] * 7 + [90]))
    assert all(a[i]["heart_rate_bpm"]["baseline"] is None for i in range(7))
    assert a[7]["heart_rate_bpm"]["baseline"] == 60


def test_baseline_excludes_current_day_and_needs_seven_valid_readings():
    a = analyze(make_series(7, heart_rate_bpm=[60] * 7))
    assert a[6]["heart_rate_bpm"]["baseline"] is None  # only 6 earlier readings


def test_flagged_readings_are_left_out_of_later_baselines():
    # day 8 (index 7) is flagged at 78; it must not pull the baseline up afterwards
    a = analyze(make_series(10, heart_rate_bpm=[60] * 7 + [78, 60, 60]))
    assert a[7]["heart_rate_bpm"]["flagged"] is True
    assert a[9]["heart_rate_bpm"]["baseline"] == 60


def test_poor_quality_and_missing_readings_are_left_out():
    s = make_series(10, spo2_pct=[97] * 3 + [80] + [97] * 6, spo2_quality=["good"] * 3 + ["poor"] + ["good"] * 6,
                    heart_rate_bpm=[60, 60, None, 60, 60, 60, 60, 60, 60, 60])
    a = analyze(s)
    assert a[9]["spo2_pct"]["baseline"] == 97          # the poor 80 is ignored
    assert a[9]["heart_rate_bpm"]["baseline"] == 60    # the missing value is ignored


def test_baseline_uses_last_seven_valid_readings():
    a = analyze(make_series(12, heart_rate_bpm=[100] * 4 + [60] * 7 + [70]))
    assert a[11]["heart_rate_bpm"]["baseline"] == 60


def test_temperature_baseline_is_per_time_window():
    stamps = [ts(i, 8) for i in range(8)] + [ts(7, 20)]          # 8 mornings, then one evening reading
    a = analyze(make_series(9, timestamp=stamps, body_temp_c=[33.5] * 8 + [35.0]))
    assert a[7]["body_temp_c"]["baseline"] == 33.5               # morning has 7 earlier mornings
    assert a[8]["body_temp_c"]["baseline"] is None               # evening has no comparable readings


def test_temperature_baseline_needs_same_sensor_location():
    locations = ["wrist"] * 8 + ["chest"]
    a = analyze(make_series(9, temp_sensor_location=locations))
    assert a[7]["body_temp_c"]["baseline"] == 33.5
    assert a[8]["body_temp_c"]["baseline"] is None


def test_preflight_baseline_is_used_when_series_has_none(monkeypatch):
    monkeypatch.setattr(rules_config, "PREFLIGHT_BASELINE", {"heart_rate_bpm": 62})
    a = analyze(make_series(3, heart_rate_bpm=[62, 62, 80]))
    assert a[2]["heart_rate_bpm"]["baseline"] == 62
    assert a[2]["heart_rate_bpm"]["flagged"] is True


def test_time_windows():
    assert time_window("2026-11-01T03:00:00Z") == "overnight"
    assert time_window("2026-11-01T08:00:00Z") == "morning"
    assert time_window("2026-11-01T14:00:00Z") == "afternoon"
    assert time_window("2026-11-01T20:00:00Z") == "evening"


def test_trend_slope_direction():
    assert trend_slope([1, 2, 3, 4]) > 0
    assert trend_slope([4, 3, 2, 1]) < 0
    assert trend_slope([5, 5, 5]) == 0
    assert trend_slope([5]) == 0
