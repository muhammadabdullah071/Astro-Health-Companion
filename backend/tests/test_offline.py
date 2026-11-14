"""Offline behaviour, executed rather than assumed (task Section 10).

Every socket connection to a non-loopback address is blocked inside the test process,
then the monitoring API and the local RAG assistant are exercised. If an endpoint
needed the internet, these tests would fail naming the blocked host.

What this proves, precisely:
* the exercised code paths open no outbound TCP connection (the fixture records any
  attempt and the assertions fail if the list is non-empty);
* the assistant still answers offline, citing the S1-S9 sources documented for the
  rule that fired.

What it does NOT prove, stated plainly:
* the guard patches socket.socket.connect, so it blocks TCP connections (urllib and
  http.client included) but not DNS lookups, connect_ex, or raw sockets;
* it is NOT a Wi-Fi-off test. Switching the machine offline and starting the server
  is a manual check and is still required.
"""
from __future__ import annotations

import socket
import sys

import pytest

from app import config
from app.services import rag_adapter

if str(config.REPO_ROOT) not in sys.path:  # rag/ lives at the repository root
    sys.path.insert(0, str(config.REPO_ROOT))

from rag.ask import RULE_SOURCE_MAP  # noqa: E402  (needs the sys.path entry above)

LOOPBACK = {"127.0.0.1", "::1", "localhost"}
ASK = {"question": "Why was this flagged?", "alert_id": "a1"}

# Ammara's Section 3 rule -> source mapping, repeated here as INDEPENDENT evidence so
# the grounding test cannot pass merely because the RAG module agrees with itself.
EXPECTED_SOURCES = {
    "HR-01": {"S2", "S4"},
    "HR-02": {"S3", "S5"},
    "SPO2-01": {"S4"},
    "SLEEP-01": {"S7"},
    "SLEEP-02": {"S7"},
    "TEMP-01": {"S4", "S6"},
    "DATA-01": {"S4"},
    "DATA-02": {"S3", "S4"},
}
RULE_METRIC = {
    "HR-01": "heart_rate_bpm",
    "HR-02": "heart_rate_bpm",
    "SPO2-01": "spo2_pct",
    "SLEEP-01": "sleep_hours",
    "SLEEP-02": "sleep_hours",
    "TEMP-01": "body_temp_c",
    "DATA-01": "spo2_pct",
    "DATA-02": "heart_rate_bpm",
}


@pytest.fixture()
def blocked_hosts(monkeypatch):
    """Refuse any connection that leaves this machine and record the attempt."""
    real_connect = socket.socket.connect
    attempts = []

    def guarded_connect(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if isinstance(host, str) and host not in LOOPBACK:
            attempts.append(host)
            raise OSError(f"offline test: blocked connection to {host}")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    return attempts


@pytest.fixture(autouse=True)
def no_local_model(monkeypatch):
    """Point the optional model at a dead loopback port so the answer path is deterministic."""
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:1")


def cited_source_ids(citations):
    """'S2: Tomsia ...' -> 'S2'."""
    return {c["title"].split(":")[0].strip() for c in citations if ":" in c.get("title", "")}


def alert_for(rule_id):
    return {
        "rule_id": rule_id,
        "rule": f"Prototype alert for {rule_id}",
        "severity": "notice",
        "category": "physiological",
        "metric": RULE_METRIC[rule_id],
        "message": "A prototype rule fired in a test.",
        "next_step": "Repeat the measurement and follow mission procedure.",
    }


def test_monitoring_api_works_without_any_external_connection(client, blocked_hosts):
    assert client.get("/api/status").status_code == 200
    assert client.get("/api/profile").status_code == 200
    assert len(client.get("/api/readings?days=14").json()["readings"]) == 14
    assert client.get("/api/alerts").status_code == 200
    answer = client.post("/api/assistant/ask", json=ASK).json()
    assert cited_source_ids(answer["citations"]) >= EXPECTED_SOURCES["HR-01"]
    assert blocked_hosts == [], f"the app tried to reach the internet: {blocked_hosts}"


def test_status_reports_offline_mode_and_still_answers(client, blocked_hosts):
    status = client.get("/api/status").json()
    assert status["backend"] == "ok"
    assert status["offline_mode"] is True
    assert status["last_data_update"] == "2026-11-14T08:00:00Z"
    assert status["data_label"] == "SIMULATED"


def test_rag_rule_source_map_matches_the_documented_mapping():
    """Drift guard: the retrieval map must still be Ammara's Section 3 mapping."""
    documented = {rule: set(ids) for rule, ids in RULE_SOURCE_MAP.items() if "-" in rule}
    assert documented == EXPECTED_SOURCES


@pytest.mark.parametrize("rule_id", sorted(EXPECTED_SOURCES))
def test_alert_answers_cite_the_sources_mapped_to_that_rule(blocked_hosts, rule_id):
    """Grounding, not formatting: the citation set must contain the mapped source ids."""
    answer = rag_adapter.answer_question("Why was this flagged?", alert_for(rule_id))
    assert answer["mode"] == "retrieval_only"
    assert cited_source_ids(answer["citations"]) >= EXPECTED_SOURCES[rule_id], (
        f"{rule_id} should cite {sorted(EXPECTED_SOURCES[rule_id])}, "
        f"got {sorted(cited_source_ids(answer['citations']))}"
    )


def test_no_placeholder_citations_remain_in_the_answer_path(client, blocked_hosts):
    """Regression guard: the old example.org stub must never come back."""
    answer = client.post("/api/assistant/ask", json=ASK).json()
    for citation in answer["citations"]:
        assert "example.org" not in citation["url"]
        assert "PLACEHOLDER" not in citation["title"].upper()


def test_a_question_outside_the_library_returns_no_evidence(client, blocked_hosts):
    answer = client.post("/api/assistant/ask", json={"question": "What is the weather on Mars?"}).json()
    assert answer["citations"] == []
    assert "cannot answer" in answer["answer"].lower()


def test_temperature_alert_answer_keeps_the_clinical_boundary(client, blocked_hosts):
    """A fever question about a skin reading must not become a diagnosis."""
    answer = rag_adapter.answer_question(
        "Should I be worried about a fever?",
        {
            "rule_id": "TEMP-01",
            "rule": "Skin temperature above personal baseline",
            "severity": "watch",
            "category": "physiological",
            "metric": "body_temp_c",
            "message": "Skin temperature is 34.1 °C, 0.6 °C above this astronaut's skin baseline of 33.5 °C.",
            "next_step": "Repeat with the same site and method.",
        },
    )
    text = answer["answer"].lower()
    assert answer["mode"] == "retrieval_only"
    assert "not a core-temperature measurement" in text
    assert "not a diagnosis" in text
