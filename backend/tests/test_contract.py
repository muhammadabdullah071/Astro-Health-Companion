"""Live responses must have the same fields as contract/examples (the frozen v1 contract)."""
import json

from app import config


def example(name):
    return json.loads((config.examples_dir() / f"{name}.json").read_text(encoding="utf-8"))


def same_shape(live, ex, path="$"):
    if isinstance(ex, dict):
        assert isinstance(live, dict), f"{path} should be an object"
        assert set(live) == set(ex), f"{path}: fields differ. live={sorted(live)} contract={sorted(ex)}"
        for k in ex:
            same_shape(live[k], ex[k], f"{path}.{k}")
    elif isinstance(ex, list) and ex and live:
        same_shape(live[0], ex[0], f"{path}[0]")


def test_status(client):
    same_shape(client.get("/api/status").json(), example("status"))


def test_profile(client):
    same_shape(client.get("/api/profile").json(), example("profile"))


def test_readings(client):
    same_shape(client.get("/api/readings?days=14").json(), example("readings"))


def test_alerts(client):
    same_shape(client.get("/api/alerts").json(), example("alerts"))


def test_assistant(client):
    body = json.loads((config.examples_dir() / "assistant_ask_request.json").read_text())
    same_shape(client.post("/api/assistant/ask", json=body).json(), example("assistant_ask"))


def test_error(client):
    body = {"question": "x", "alert_id": "zzz"}
    same_shape(client.post("/api/assistant/ask", json=body).json(), example("error"))
