from app.engine.baseline import consecutive_below, rolling_baseline, trend_slope
from tests.helpers import make_series


def test_baseline_excludes_current_day():
    s = make_series(8, heart_rate_bpm=[60] * 7 + [90])
    assert rolling_baseline(s, 7, "heart_rate_bpm") == 60


def test_baseline_uses_available_days_when_fewer_than_window():
    s = make_series(5, heart_rate_bpm=[60, 62, 64, 66, 99])
    assert rolling_baseline(s, 4, "heart_rate_bpm") == 63  # mean of first four


def test_baseline_none_when_too_few_days():
    s = make_series(3, heart_rate_bpm=[60, 62, 99])
    assert rolling_baseline(s, 2, "heart_rate_bpm") is None  # only 2 prior days


def test_baseline_window_is_seven_days():
    s = make_series(12, heart_rate_bpm=[100] * 4 + [60] * 7 + [70])
    assert rolling_baseline(s, 11, "heart_rate_bpm") == 60


def test_consecutive_below():
    s = make_series(5, sleep_hours=[7, 7, 5.9, 5.8, 5.5])
    assert consecutive_below(s, 4, "sleep_hours", 6.0, 3)
    assert not consecutive_below(s, 4, "sleep_hours", 6.0, 4)
    assert not consecutive_below(s, 1, "sleep_hours", 6.0, 3)  # not enough history


def test_trend_slope_direction():
    assert trend_slope([1, 2, 3, 4]) > 0
    assert trend_slope([4, 3, 2, 1]) < 0
    assert trend_slope([5, 5, 5]) == 0
    assert trend_slope([5]) == 0
