import sqlite3

import pytest

from app import config
from app.db import seed

SAMPLE = config.sample_csv_path().parent


def test_seed_loads_both_profiles_and_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "s.db"))
    first = seed.seed()
    second = seed.seed()
    assert first == second
    assert first["astronaut_id"] == "ASTRO-01" and first["readings"] == 30 and first["alerts"] == 10
    assert first["profiles"] == {"ASTRO-01": {"readings": 30, "alerts": 10},
                                 "ASTRO-02": {"readings": 30, "alerts": 7}}
    conn = sqlite3.connect(config.db_path())
    assert conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0] == 60
    assert conn.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 2


def test_same_alert_id_can_exist_for_both_profiles(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "ids.db"))
    seed.seed()
    conn = sqlite3.connect(config.db_path())
    assert conn.execute("SELECT COUNT(*) FROM alerts WHERE id = 'a1'").fetchone()[0] == 2


def test_quality_sidecar_is_stored_per_profile(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "q.db"))
    seed.seed()
    conn = sqlite3.connect(config.db_path())
    poor = conn.execute("SELECT astronaut_id, ts, spo2_pct FROM readings WHERE spo2_quality = 'poor'").fetchall()
    assert poor == [("ASTRO-01", "2026-11-06T08:00:00Z", 93.0)]
    assert conn.execute("SELECT DISTINCT temp_sensor_location, temp_device_id FROM readings").fetchall() == \
        [("left_wrist", "SIM-WEARABLE-01")]


def test_seed_single_csv_without_sidecar_uses_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "plain.db"))
    csv = tmp_path / "plain.csv"      # only the 5 core columns
    csv.write_text("timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c\n2026-11-01T08:00:00Z,62,97,7.0,33.5\n")
    result = seed.seed(csv)
    assert result["profiles"] == {"ASTRO-01": {"readings": 1, "alerts": 1}}      # DATA-02 only
    row = sqlite3.connect(config.db_path()).execute(
        "SELECT hr_quality, spo2_quality, sleep_source, temp_sensor_location, temp_device_id, "
        "temp_contact_quality, temp_dropout FROM readings").fetchone()
    assert row == ("good", "good", "wearable", "wrist", "wearable-01", "good", 0)


def test_seed_single_csv_with_traceability_gives_data_01(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "t.db"))
    without = seed.seed(SAMPLE / "readings.csv")
    with_sidecar = seed.seed(SAMPLE / "readings.csv", SAMPLE / "traceability.csv")
    assert with_sidecar["alerts"] == without["alerts"] + 1            # DATA-01 on day 22


def test_quality_column_inside_the_csv_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "p.db"))
    csv = tmp_path / "poor.csv"
    csv.write_text("timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c,spo2_quality\n"
                   "2026-11-01T08:00:00Z,62,80,7.0,33.5,poor\n")
    seed.seed(csv)
    conn = sqlite3.connect(config.db_path())
    assert conn.execute("SELECT spo2_pct, spo2_quality FROM readings").fetchone() == (80.0, "poor")   # stored, not dropped
    assert conn.execute("SELECT 1 FROM alerts WHERE rule_id = 'DATA-01'").fetchone() is not None


def test_seed_falls_back_to_examples_json(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "f.db"))
    monkeypatch.setenv("ASTRO_SAMPLE_CSV", str(tmp_path / "missing.csv"))
    assert seed.seed()["readings"] == 14


def test_unknown_astronaut_id_is_a_clear_error(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "e.db"))
    monkeypatch.setenv("ASTRO_ID", "ASTRO-99")
    with pytest.raises(ValueError, match="ASTRO-99"):
        seed.seed()
