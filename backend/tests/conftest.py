import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ASTRO_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path / "no-index"))
    from app.main import create_app

    with TestClient(create_app()) as c:  # lifespan seeds the temp database
        yield c
