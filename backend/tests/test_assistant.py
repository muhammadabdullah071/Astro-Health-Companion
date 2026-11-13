import time

from app.services import rag_adapter

ASK = {"question": "Why was this flagged?", "alert_id": "a1"}


def test_ask_with_alert_returns_contract_fields(client):
    r = client.post("/api/assistant/ask", json=ASK).json()
    assert set(r) == {"answer", "mode", "citations", "disclaimer"}
    assert r["mode"] in ("llm", "retrieval_only") and r["citations"]
    assert r["disclaimer"] == "Decision support only - not a medical diagnosis."


def test_unknown_alert_is_404_with_error_shape(client):
    r = client.post("/api/assistant/ask", json={"question": "Why?", "alert_id": "zzz"})
    assert r.status_code == 404 and r.json() == {"error": {"code": "NOT_FOUND", "message": "Alert not found."}}


def test_empty_question_is_422(client):
    r = client.post("/api/assistant/ask", json={"question": ""})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_question_without_alert_gets_honest_limitation(client):
    r = client.post("/api/assistant/ask", json={"question": "What is the weather on Mars?"}).json()
    assert "cannot answer" in r["answer"] and r["citations"] == []


def test_timeout_falls_back_to_retrieval_only(client, monkeypatch):
    monkeypatch.setenv("ASK_TIMEOUT_SECONDS", "0.2")
    monkeypatch.setattr(rag_adapter, "get_ask", lambda: (lambda q, a: time.sleep(1.5)))
    start = time.time()
    r = client.post("/api/assistant/ask", json=ASK)
    assert r.status_code == 200 and r.json()["mode"] == "retrieval_only"
    assert time.time() - start < 1.2


def test_exception_falls_back_to_retrieval_only(client, monkeypatch):
    def boom(q, a):
        raise RuntimeError("model crashed")

    monkeypatch.setattr(rag_adapter, "get_ask", lambda: boom)
    r = client.post("/api/assistant/ask", json=ASK)
    assert r.status_code == 200 and r.json()["mode"] == "retrieval_only"


def test_invalid_rag_response_falls_back(client, monkeypatch):
    monkeypatch.setattr(rag_adapter, "get_ask", lambda: (lambda q, a: "not a dict"))
    assert client.post("/api/assistant/ask", json=ASK).json()["mode"] == "retrieval_only"


def test_good_llm_response_is_normalised(client, monkeypatch):
    good = {"answer": "ok", "mode": "llm", "citations": [{"title": "T", "url": "u"}]}
    monkeypatch.setattr(rag_adapter, "get_ask", lambda: (lambda q, a: good))
    r = client.post("/api/assistant/ask", json=ASK).json()
    assert r["mode"] == "llm"
    assert set(r["citations"][0]) == {"title", "source", "url", "excerpt"}


def test_alert_dict_is_passed_to_ask(client, monkeypatch):
    seen = {}

    def spy(q, a):
        seen.update(a)
        return {"answer": "x", "mode": "llm", "citations": []}

    monkeypatch.setattr(rag_adapter, "get_ask", lambda: spy)
    client.post("/api/assistant/ask", json=ASK)
    assert seen["id"] == "a1" and seen["rule_id"] == "HR-01" and seen["next_step"]
    assert seen["category"] == "physiological" and seen["source"].startswith("Prototype rule")
