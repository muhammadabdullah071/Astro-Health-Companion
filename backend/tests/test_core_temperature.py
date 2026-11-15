"""Manual CORE temperature: separate storage, never used by skin baselines or alerts, never a fever label."""
import sqlite3

import pytest

from app import config
from app.db import database, seed
from tests.test_contract import example, same_shape

NOW = "2026-11-14T12:00:00Z"
GOOD = {"core_temp_c": 37.1, "method": "oral", "timestamp": "2026-11-14T09:30:00Z", "note": "after exercise"}


@pytest.fixture(autouse=True)
def pinned_clock(monkeypatch):
    monkeypatch.setenv("ASTRO_NOW", NOW)


def post(client, **overrides):
    return client.post("/api/core-temperature", json={**GOOD, **overrides})


def test_post_stores_an_entry_and_returns_the_contract_shape(client):
    r = post(client)
    assert r.status_code == 201
    same_shape(r.json(), example("core_temperature"))
    entry = r.json()["entry"]
    assert entry["temp_type"] == "core" and entry["measurement_method"] == "manual"
    assert entry["core_temp_c"] == 37.1 and entry["timestamp"] == "2026-11-14T09:30:00Z"
    listing = client.get("/api/core-temperature").json()
    same_shape(listing, example("core_temperature_list"))
    assert [e["id"] for e in listing["entries"]] == [entry["id"]]


def test_default_time_is_now_and_offsets_are_converted_to_utc(client):
    assert post(client, timestamp=None).json()["entry"]["timestamp"] == NOW
    assert post(client, timestamp="2026-11-14T11:00:00+02:00").json()["entry"]["timestamp"] == "2026-11-14T09:00:00Z"


def test_listing_is_oldest_first_and_limited(client):
    for stamp in ("2026-11-14T10:00:00Z", "2026-11-13T10:00:00Z", "2026-11-12T10:00:00Z"):
        post(client, timestamp=stamp)
    times = [e["timestamp"] for e in client.get("/api/core-temperature").json()["entries"]]
    assert times == sorted(times)
    newest_two = client.get("/api/core-temperature?limit=2").json()["entries"]
    assert [e["timestamp"] for e in newest_two] == ["2026-11-13T10:00:00Z", "2026-11-14T10:00:00Z"]


@pytest.mark.parametrize("bad", [
    {"core_temp_c": 29.9}, {"core_temp_c": 45.1}, {"core_temp_c": "warm"}, {"method": "psychic"},
    {"timestamp": "yesterday"}, {"timestamp": "2026-11-14T09:30:00"}, {"timestamp": "2026-11-15T12:00:00Z"},
    {"note": "x" * 201},
])
def test_invalid_entries_are_rejected_with_the_standard_error_shape(client, bad):
    r = post(client, **bad)
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get("/api/core-temperature").json()["entries"] == []


def test_missing_required_fields_are_rejected(client):
    assert client.post("/api/core-temperature", json={"method": "oral"}).status_code == 422
    assert client.post("/api/core-temperature", json={"core_temp_c": 37.0}).status_code == 422


def test_core_entries_change_no_reading_baseline_alert_or_status(client):
    before = {p: client.get(p).json() for p in ("/api/readings?days=30", "/api/alerts?days=30", "/api/status")}
    assert post(client, core_temp_c=39.4).status_code == 201     # a high value must still not raise anything
    after = {p: client.get(p).json() for p in before}
    assert after == before


def test_core_values_live_in_their_own_table_never_in_readings(client):
    post(client)
    conn = sqlite3.connect(config.db_path())
    try:
        readings_cols = [r[1] for r in conn.execute("PRAGMA table_info(readings)")]
        assert not any("core" in c for c in readings_cols)
        assert conn.execute("SELECT COUNT(*) FROM core_temperatures").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM readings WHERE body_temp_c = 37.1").fetchone()[0] == 0
    finally:
        conn.close()


def test_responses_never_claim_a_diagnosis_or_fever(client):
    text = (post(client, core_temp_c=39.4).text + client.get("/api/core-temperature").text).lower()
    assert "fever" not in text and "infection" not in text
    assert "not a diagnosis" in text


def test_an_existing_database_without_the_table_is_upgraded_on_start(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import create_app

    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "old.db"))
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path / "no-index"))
    seed.seed()
    conn = sqlite3.connect(config.db_path())
    conn.execute("DROP TABLE core_temperatures")
    conn.commit()
    conn.close()
    with TestClient(create_app()) as c:           # lifespan sees an existing db and adds the table
        assert post(c).status_code == 201


def test_reseeding_clears_manual_entries_like_the_rest_of_the_demo_data(client):
    post(client)
    seed.seed()
    assert client.get("/api/core-temperature").json()["entries"] == []
    assert database.CORE_TEMPERATURE_SQL.exists()
