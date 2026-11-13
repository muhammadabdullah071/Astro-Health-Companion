def test_readings_default_is_14_days_oldest_first_and_labelled(client):
    r = client.get("/api/readings").json()
    assert r["data_label"] == "SIMULATED"
    ts = [x["timestamp"] for x in r["readings"]]
    assert len(ts) == 14 and ts == sorted(ts)


def test_readings_days_param(client):
    assert len(client.get("/api/readings?days=7").json()["readings"]) == 7
    assert len(client.get("/api/readings?days=30").json()["readings"]) == 30


def test_readings_rejects_bad_days_with_error_shape(client):
    r = client.get("/api/readings?days=0")
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_demo_alerts_are_deterministic(client):
    alerts = client.get("/api/alerts").json()["alerts"]
    assert [a["id"] for a in alerts] == ["a1", "a2"]
    hr, sleep = alerts
    assert hr["metric"] == "heart_rate_bpm" and hr["severity"] == "watch" and hr["value"] == 78
    assert 15 <= hr["value"] - hr["baseline"] <= 18
    assert sleep["metric"] == "sleep_hours" and sleep["severity"] == "notice"


def test_profile_has_mission_day(client):
    p = client.get("/api/profile").json()
    assert p["mission_day"] == 143 and p["data_label"] == "SIMULATED"


def test_unknown_route_uses_error_shape(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_cors_allows_frontend_origin(client):
    r = client.get("/api/status", headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
