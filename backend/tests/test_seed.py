import sqlite3

from app import config
from app.db import seed


def test_seed_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "s.db"))
    first = seed.seed()
    second = seed.seed()
    assert first["readings"] == second["readings"] == 26
    assert first["alerts"] == second["alerts"] == 9
    conn = sqlite3.connect(config.db_path())
    assert conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0] == 26
    assert conn.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 1


def test_seed_stores_quality_columns_with_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "q.db"))
    csv = tmp_path / "plain.csv"      # only the 5 core columns, like a minimal file from Sofia
    csv.write_text("timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c\n2026-11-01T08:00:00Z,62,97,7.0,33.5\n")
    seed.seed(csv)
    row = sqlite3.connect(config.db_path()).execute(
        "SELECT hr_quality, spo2_quality, sleep_source, temp_sensor_location, temp_device_id, "
        "temp_contact_quality, temp_dropout FROM readings").fetchone()
    assert row == ("good", "good", "wearable", "wrist", "wearable-01", "good", 0)


def test_seed_keeps_poor_quality_readings_but_flags_them(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "p.db"))
    csv = tmp_path / "poor.csv"
    csv.write_text("timestamp,heart_rate_bpm,spo2_pct,sleep_hours,body_temp_c,spo2_quality\n"
                   "2026-11-01T08:00:00Z,62,80,7.0,33.5,poor\n")
    result = seed.seed(csv)
    assert result["readings"] == 1       # stored, not dropped
    conn = sqlite3.connect(config.db_path())
    assert conn.execute("SELECT spo2_pct, spo2_quality FROM readings").fetchone() == (80.0, "poor")
    assert conn.execute("SELECT rule_id FROM alerts WHERE rule_id = 'DATA-01'").fetchone() is not None


def test_seed_falls_back_to_examples_json(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "f.db"))
    monkeypatch.setenv("ASTRO_SAMPLE_CSV", str(tmp_path / "missing.csv"))
    assert seed.seed()["readings"] == 14
