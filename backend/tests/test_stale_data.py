"""DATA-01 stale-data detection (spec: "missing, stale, badly formatted, or poor-quality").

Staleness depends on the clock, so it is NOT part of evaluate()/evaluate_all() (pure, run at seed time).
It is judged per request by rules.stale_data_alert() and added to /api/alerts when STALE_CHECK is on.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.engine import rules
from tests.helpers import make_series, ts
from tests.test_contract import example, same_shape

NOW_FRESH = "2026-11-14T20:00:00Z"   # 12 h after the newest demo reading
NOW_STALE = "2026-11-20T08:00:00Z"   # 6 days after it


def utc(text):
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


# ------------------------------------------------------------------ engine
def test_year_old_data_is_stale():
    year_old = [row["timestamp"].replace("2026", "2025") for row in make_series(9)]
    series = make_series(9, timestamp=year_old)
    a = rules.stale_data_alert(series, utc("2026-11-15T08:00:00Z"))
    assert a and a["rule_id"] == "DATA-01" and a["severity"] == "notice"
    assert a["category"] == "data_quality" and a["data_quality"] == "insufficient"
    assert a["value"] is None and a["baseline"] is None
    assert "No health event is inferred" in a["message"] and "days" in a["message"]
    assert a["timestamp"] == series[-1]["timestamp"]


def test_threshold_is_the_data01_gap_hours():
    series = make_series(9)
    last = utc(series[-1]["timestamp"])
    assert rules.stale_data_alert(series, last + timedelta(hours=24)) is None
    assert rules.stale_data_alert(series, last + timedelta(hours=36)) is None          # exactly 36 h: still fine
    assert rules.stale_data_alert(series, last + timedelta(hours=36, minutes=6)) is not None


def test_future_dated_data_is_not_stale_and_empty_series_is_ignored():
    series = make_series(9)
    assert rules.stale_data_alert(series, utc(series[-1]["timestamp"]) - timedelta(days=2)) is None
    assert rules.stale_data_alert([], utc(NOW_STALE)) is None


def test_stale_check_respects_a_disabled_data01_rule():
    cfg = {"DATA-01": {**rules.rc.RULES_CONFIG["DATA-01"], "enabled": False}}
    assert rules.stale_data_alert(make_series(9), utc(NOW_STALE), cfg) is None


def test_evaluate_stays_a_pure_function_of_the_readings():
    """Old data produces no stale alert from evaluate(): the notice is added per request, not at seed time."""
    year_old = [row["timestamp"].replace("2026", "2025") for row in make_series(9)]
    series = make_series(9, timestamp=year_old, heart_rate_bpm=[62] * 9)
    assert not any(a["rule_id"] == "DATA-01" for a in rules.evaluate_all(series))


# --------------------------------------------------------------------- API
@pytest.fixture()
def stale_on(monkeypatch):
    monkeypatch.setenv("STALE_CHECK", "true")


def stale_ids(client):
    return [a["id"] for a in client.get("/api/alerts").json()["alerts"] if a["id"] == rules.STALE_ALERT_ID]


def test_check_is_off_by_default_so_the_demo_never_goes_stale(client, monkeypatch):
    monkeypatch.setenv("ASTRO_NOW", NOW_STALE)
    assert stale_ids(client) == []
    assert client.post("/api/assistant/ask", json={"question": "why?", "alert_id": "s1"}).status_code == 404


def test_fresh_data_raises_no_notice_even_when_enabled(client, stale_on, monkeypatch):
    monkeypatch.setenv("ASTRO_NOW", NOW_FRESH)
    assert stale_ids(client) == []


def test_stale_notice_is_listed_after_watch_alerts_and_before_other_notices(client, stale_on, monkeypatch):
    monkeypatch.setenv("ASTRO_NOW", NOW_STALE)
    alerts = client.get("/api/alerts?days=14").json()["alerts"]
    ids = [a["id"] for a in alerts]
    assert "s1" in ids
    stale = alerts[ids.index("s1")]
    assert stale["rule_id"] == "DATA-01" and stale["data_label"] == "SIMULATED"
    same_shape(stale, example("alerts")["alerts"][0])
    ranks = [{"attention": 3, "watch": 2, "notice": 1}[a["severity"]] for a in alerts]
    assert ranks == sorted(ranks, reverse=True), "most severe first"
    assert alerts[ids.index("s1") - 1]["severity"] in ("watch", "attention")


def test_stale_notice_does_not_renumber_the_stored_alert_ids(client, stale_on, monkeypatch):
    before = [a["id"] for a in client.get("/api/alerts").json()["alerts"]]
    monkeypatch.setenv("ASTRO_NOW", NOW_STALE)
    after = [a["id"] for a in client.get("/api/alerts").json()["alerts"] if a["id"] != "s1"]
    assert after == before


def test_assistant_can_explain_the_stale_notice(client, stale_on, monkeypatch):
    monkeypatch.setenv("ASTRO_NOW", NOW_STALE)
    r = client.post("/api/assistant/ask", json={"question": "Why is my data flagged?", "alert_id": "s1"})
    assert r.status_code == 200
    assert "infer no health event" in r.json()["answer"].lower() or "no health event" in r.json()["answer"].lower()
    monkeypatch.setenv("ASTRO_NOW", NOW_FRESH)
    assert client.post("/api/assistant/ask", json={"question": "why?", "alert_id": "s1"}).status_code == 404


def test_invalid_astro_now_falls_back_to_the_real_clock(client, stale_on, monkeypatch):
    monkeypatch.setenv("ASTRO_NOW", "not-a-date")
    assert client.get("/api/alerts").status_code == 200
