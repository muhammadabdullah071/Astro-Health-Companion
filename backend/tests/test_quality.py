import pytest

from app.engine import rules_config
from app.engine.quality import reading_issue, valid_value
from tests.helpers import make_series


def row(**kw):
    return make_series(1, **{k: [v] for k, v in kw.items()})[0]


def test_good_reading_is_valid():
    assert reading_issue(row(), "heart_rate_bpm") is None
    assert valid_value(row(), "spo2_pct") == 97.0


def test_missing_value():
    assert reading_issue(row(heart_rate_bpm=None), "heart_rate_bpm") == "missing"
    assert valid_value(row(heart_rate_bpm=None), "heart_rate_bpm") is None


def test_poor_quality_hr_and_spo2():
    assert reading_issue(row(hr_quality="poor"), "heart_rate_bpm") == "poor_quality"
    assert reading_issue(row(spo2_quality="poor"), "spo2_pct") == "poor_quality"


def test_skin_temperature_validity_rules():
    assert reading_issue(row(body_temp_c=33.5), "body_temp_c") is None
    assert reading_issue(row(body_temp_c=39.0), "body_temp_c") == "poor_quality"      # above 38
    assert reading_issue(row(body_temp_c=27.0), "body_temp_c") == "poor_quality"      # below 28
    assert reading_issue(row(temp_contact_quality="poor"), "body_temp_c") == "poor_quality"
    assert reading_issue(row(temp_dropout=1), "body_temp_c") == "poor_quality"
    assert reading_issue(row(temp_sensor_location=""), "body_temp_c") == "poor_quality"
    assert reading_issue(row(temp_device_id=""), "body_temp_c") == "poor_quality"


def test_rows_without_quality_columns_use_defaults():
    plain = {"timestamp": "2026-11-01T08:00:00Z", "heart_rate_bpm": 62, "spo2_pct": 97,
             "sleep_hours": 7.0, "body_temp_c": 33.5}
    assert all(reading_issue(plain, m) is None for m in ("heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c"))


def test_temp_threshold_must_cover_sensor_accuracy_and_noise():
    rules_config.validate_config()  # the shipped config is valid
    bad = {k: dict(v) for k, v in rules_config.RULES_CONFIG.items()}
    bad["TEMP-01"]["temp_delta_threshold"] = 0.2
    with pytest.raises(ValueError):
        rules_config.validate_config(bad)
