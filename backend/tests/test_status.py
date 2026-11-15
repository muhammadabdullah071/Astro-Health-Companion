import json

from app.services import health


def test_status_reflects_real_checks(client, monkeypatch, tmp_path):
    monkeypatch.setattr(health, "probe_llm", lambda *a, **k: False)
    s = client.get("/api/status").json()
    assert s["backend"] == "ok" and s["llm"] == "unavailable"
    # An empty RAG_INDEX_DIR is initialised at startup with the default S1-S9 corpus, not reported as 0
    assert s["documents_indexed"] == 9
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


def _fresh_client(monkeypatch, tmp_path, rag_index_dir):
    from fastapi.testclient import TestClient

    from app.main import create_app

    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "fresh.db"))
    monkeypatch.setenv("RAG_INDEX_DIR", str(rag_index_dir))
    return TestClient(create_app())


def test_fresh_rag_index_dir_is_initialised_at_startup(monkeypatch, tmp_path):
    """Fresh clone / new RAG_INDEX_DIR: startup writes corpus.json + meta.json there and reports 9 sources."""
    idx = tmp_path / "custom-index"
    with _fresh_client(monkeypatch, tmp_path, idx) as c:
        s = c.get("/api/status").json()
    assert s["documents_indexed"] == 9
    meta = json.loads((idx / "meta.json").read_text(encoding="utf-8"))
    assert meta["documents_indexed"] == 9
    assert len(json.loads((idx / "corpus.json").read_text(encoding="utf-8"))) == 9


def test_relative_rag_index_dir_resolves_against_repo_root(monkeypatch, tmp_path):
    from app import config

    rel = f"data/runtime/test-rag-index-{tmp_path.name}"
    target = config.REPO_ROOT / rel
    try:
        assert config.rag_index_dir() != target  # sanity: env not set yet
        with _fresh_client(monkeypatch, tmp_path, rel) as c:
            assert c.get("/api/status").json()["documents_indexed"] == 9
        assert config.rag_index_dir() == target
        assert (target / "meta.json").is_file()
    finally:
        import shutil

        shutil.rmtree(target, ignore_errors=True)
