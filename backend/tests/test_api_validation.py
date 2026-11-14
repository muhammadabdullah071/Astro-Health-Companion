"""API validation checks the contract shape test cannot see (task Section 7).

Complements tests/test_endpoints.py (which owns endpoint behaviour and the demo
payloads) by covering HTTP method handling, query/body validation, response types,
documented units, severity vocabulary and citation shape.
"""
from __future__ import annotations

import pytest

from app import config
from app.services import health

SEVERITY_RANK = {"notice": 1, "watch": 2, "attention": 3}


@pytest.fixture(autouse=True)
def no_local_model(monkeypatch):
    """Keep assistant checks deterministic and fast: never call a real model server."""
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")


# --------------------------------------------------------------- HTTP methods
@pytest.mark.parametrize(
    "method,path",
    [("post", "/api/status"), ("get", "/api/assistant/ask"), ("put", "/api/readings"), ("delete", "/api/alerts")],
)
def test_unsupported_methods_return_405_with_the_error_shape(client, method, path):
    response = getattr(client, method)(path)
    assert response.status_code == 405
    body = response.json()["error"]
    assert body["code"] == "METHOD_NOT_ALLOWED" and body["message"]


# ------------------------------------------------------------- query validation
@pytest.mark.parametrize("path", ["/api/readings", "/api/alerts"])
@pytest.mark.parametrize("days", ["0", "91", "-1", "abc", "1.5", ""])
def test_invalid_days_is_rejected_on_both_list_endpoints(client, path, days):
    response = client.get(f"{path}?days={days}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_documented_days_boundaries_are_accepted(client):
    assert len(client.get("/api/readings?days=1").json()["readings"]) == 1
    assert len(client.get("/api/readings?days=90").json()["readings"]) == 30
    assert client.get("/api/alerts?days=1").status_code == 200
    assert client.get("/api/alerts?days=90").status_code == 200


# ------------------------------------------------------------ body validation
@pytest.mark.parametrize(
    "body", [{}, {"alert_id": "a1"}, {"question": ""}, {"question": "x" * 1001}],
)
def test_assistant_rejects_invalid_bodies(client, body):
    response = client.post("/api/assistant/ask", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_assistant_rejects_a_malformed_json_body(client):
    response = client.post(
        "/api/assistant/ask", content=b"{not json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_assistant_tolerates_unknown_extra_fields(client):
    """A frontend sending extra keys must not break the endpoint."""
    response = client.post(
        "/api/assistant/ask", json={"question": "Why was this flagged?", "alert_id": "a1", "extra": 1}
    )
    assert response.status_code == 200


def test_blank_question_is_answered_honestly_instead_of_guessing(client):
    """Only an empty string is rejected; a whitespace-only question gets the honest limitation."""
    body = client.post("/api/assistant/ask", json={"question": "   "}).json()
    assert body["citations"] == []
    assert "cannot answer" in body["answer"].lower()
    assert body["disclaimer"] == config.DISCLAIMER


# --------------------------------------------------------------------- /status
def test_status_types_and_vocabulary_are_meaningful(client, monkeypatch):
    monkeypatch.setattr(health, "probe_llm", lambda *a, **k: False)
    status = client.get("/api/status").json()
    assert status["backend"] == "ok"
    assert status["offline_mode"] is True
    assert status["llm"] == "unavailable"
    assert isinstance(status["documents_indexed"], int) and status["documents_indexed"] >= 0
    assert status["data_label"] == "SIMULATED"


def test_status_last_data_update_matches_the_newest_reading(client):
    newest = client.get("/api/readings?days=1").json()["readings"][-1]["timestamp"]
    assert client.get("/api/status").json()["last_data_update"] == newest


# ------------------------------------------------------------------ /readings
def test_readings_are_ascending_unique_and_in_documented_units(client):
    rows = client.get("/api/readings?days=30").json()["readings"]
    stamps = [row["timestamp"] for row in rows]
    assert stamps == sorted(stamps)
    assert len(set(stamps)) == len(stamps)
    assert all(stamp.endswith("Z") for stamp in stamps)
    for row in rows:
        assert 25 <= row["heart_rate_bpm"] <= 220
        assert 70 <= row["spo2_pct"] <= 100
        assert 0 <= row["sleep_hours"] <= 24
        assert 28 <= row["body_temp_c"] <= 38


def test_a_smaller_window_is_the_tail_of_a_bigger_one(client):
    bigger = client.get("/api/readings?days=7").json()["readings"]
    assert bigger[-3:] == client.get("/api/readings?days=3").json()["readings"]


# -------------------------------------------------------------------- /alerts
def test_alerts_are_most_severe_first_with_sequential_ids(client):
    alerts = client.get("/api/alerts?days=30").json()["alerts"]
    assert alerts
    ranks = [SEVERITY_RANK[alert["severity"]] for alert in alerts]
    assert ranks == sorted(ranks, reverse=True)
    assert [a["id"] for a in alerts] == [f"a{i}" for i in range(1, len(alerts) + 1)]


def test_alert_fields_are_typed_and_use_the_documented_vocabulary(client):
    for alert in client.get("/api/alerts?days=30").json()["alerts"]:
        assert "-" in alert["rule_id"]
        assert alert["category"] in {"physiological", "data_quality", "setup"}
        assert alert["unit"] in {"bpm", "%", "hours", "°C"}
        assert alert["value"] is None or isinstance(alert["value"], (int, float))
        assert alert["baseline_status"] in {"established", "not_established"}
        assert alert["data_quality"] in {"good", "poor", "insufficient"}
        assert alert["data_label"] == "SIMULATED"
        assert alert["timestamp"].endswith("Z")
        assert alert["message"] and alert["next_step"] and alert["source"]


def test_alert_delta_is_consistent_with_its_value_and_baseline(client):
    for alert in client.get("/api/alerts?days=30").json()["alerts"]:
        if alert["value"] is not None and alert["baseline"] is not None:
            assert alert["delta"] == pytest.approx(alert["value"] - alert["baseline"], abs=0.11)


# ----------------------------------------------------------------- /assistant
def test_every_answer_carries_the_disclaimer_and_well_formed_citations(client):
    for body in (
        {"question": "Why was this flagged?", "alert_id": "a1"},
        {"question": "Tell me about sleep in long-duration missions"},
    ):
        answer = client.post("/api/assistant/ask", json=body).json()
        assert answer["disclaimer"] == config.DISCLAIMER
        assert answer["mode"] in {"llm", "retrieval_only"}
        for citation in answer["citations"]:
            assert set(citation) == {"title", "source", "url", "excerpt"}
            assert citation["url"].startswith("http") and citation["title"] and citation["source"]
