import sqlite3

from app import config
from app.db import seed


def test_seed_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "s.db"))
    first = seed.seed()
    second = seed.seed()
    assert first["readings"] == second["readings"] == 30
    assert first["alerts"] == second["alerts"] == 2
    conn = sqlite3.connect(config.db_path())
    assert conn.execute("SELECT COUNT(*) FROM readings").fetchone()[0] == 30
    assert conn.execute("SELECT COUNT(*) FROM profile").fetchone()[0] == 1


def test_seed_falls_back_to_examples_json(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "f.db"))
    monkeypatch.setenv("ASTRO_SAMPLE_CSV", str(tmp_path / "missing.csv"))
    assert seed.seed()["readings"] == 14
