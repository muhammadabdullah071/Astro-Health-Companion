import json

from app.services import health


def test_status_reflects_real_checks(client, monkeypatch, tmp_path):
    monkeypatch.setattr(health, "probe_llm", lambda *a, **k: False)
    s = client.get("/api/status").json()
    assert s["backend"] == "ok" and s["llm"] == "unavailable"
    assert s["documents_indexed"] == 0
    assert s["last_data_update"] == "2026-11-14T08:00:00Z"
    assert s["offline_mode"] is True and s["data_label"] == "SIMULATED"


def test_status_llm_ready_and_documents_from_meta(client, monkeypatch, tmp_path):
    idx = tmp_path / "idx"
    idx.mkdir()
    (idx / "meta.json").write_text(json.dumps({"documents_indexed": 12}))
    monkeypatch.setenv("RAG_INDEX_DIR", str(idx))
    monkeypatch.setattr(health, "probe_llm", lambda *a, **k: True)
    s = client.get("/api/status").json()
    assert s["llm"] == "ready" and s["documents_indexed"] == 12


def test_offline_flag_comes_from_environment(client, monkeypatch):
    monkeypatch.setenv("OFFLINE_MODE", "false")
    assert client.get("/api/status").json()["offline_mode"] is False
