ALERT_KEYS = {
    "id", "rule_id", "rule", "severity", "category", "metric", "value", "unit", "baseline", "delta",
    "baseline_status", "timestamp", "message", "next_step", "source", "data_quality", "data_label",
    "temp_type", "sensor_location", "device", "measurement_method",
}


def test_readings_default_is_14_days_oldest_first_and_labelled(client):
    r = client.get("/api/readings").json()
    assert r["data_label"] == "SIMULATED"
    ts = [x["timestamp"] for x in r["readings"]]
    assert len(ts) == 14 and ts == sorted(ts)


def test_readings_days_param(client):
    assert len(client.get("/api/readings?days=7").json()["readings"]) == 7
    assert len(client.get("/api/readings?days=30").json()["readings"]) == 26   # the whole dataset


def test_readings_still_have_only_the_frozen_contract_fields(client):
    row = client.get("/api/readings").json()["readings"][0]
    assert set(row) == {"timestamp", "heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c"}


def test_readings_rejects_bad_days_with_error_shape(client):
    r = client.get("/api/readings?days=0")
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_demo_alerts_in_the_last_14_days(client):
    alerts = client.get("/api/alerts").json()["alerts"]
    assert [a["rule_id"] for a in alerts] == ["HR-01", "SLEEP-01"]
    assert [a["id"] for a in alerts] == ["a1", "a2"]
    hr, sleep = alerts
    assert hr["severity"] == "watch" and hr["value"] == 78 and round(hr["delta"]) == 16
    assert hr["timestamp"] == "2026-11-08T08:00:00Z"                     # day 20
    assert sleep["severity"] == "notice" and sleep["timestamp"] == "2026-11-14T08:00:00Z"   # day 26


def test_every_alert_has_all_fields_and_the_simulated_label(client):
    for a in client.get("/api/alerts").json()["alerts"]:
        assert set(a) == ALERT_KEYS and a["data_label"] == "SIMULATED"


def test_alerts_days_param_reaches_back_to_calibration_alerts(client):
    everything = client.get("/api/alerts?days=26").json()["alerts"]
    assert len(everything) == 9
    assert sum(a["rule_id"] == "DATA-02" for a in everything) == 7
    assert all(a["category"] == "setup" and a["baseline_status"] == "not_established"
               for a in everything if a["rule_id"] == "DATA-02")


def test_alerts_rejects_bad_days(client):
    assert client.get("/api/alerts?days=0").status_code == 422


def test_profile_has_mission_day(client):
    p = client.get("/api/profile").json()
    assert p["mission_day"] == 143 and p["data_label"] == "SIMULATED" and p["baseline_window_days"] == 7


def test_unknown_route_uses_error_shape(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"


def test_cors_allows_frontend_origin(client):
    r = client.get("/api/status", headers={"Origin": "http://localhost:3000"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"
