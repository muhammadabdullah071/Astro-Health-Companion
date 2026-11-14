"""Sofia's SIMULATED dataset checked against her own expected_alerts.json (data/sample/)."""
import json

from app import config
from app.db import seed
from app.engine import rules

SAMPLE = config.sample_csv_path().parent


def expected_events():
    return json.loads((SAMPLE / "expected_alerts.json").read_text(encoding="utf-8"))["expected_events"]


def evaluate():
    dataset, _ = seed.load_dataset()
    return dataset, {pid: rules.evaluate_all(rows) for pid, rows in dataset.items()}


def day_of(rows, alert):
    return [r["timestamp"] for r in rows].index(alert["timestamp"]) + 1


def test_every_event_in_expected_alerts_json_matches():
    _, alerts = evaluate()
    for ev in expected_events():
        found = [a for a in alerts[ev["profile_id"]]
                 if a["rule_id"] == ev["rule_id"] and a["timestamp"] == ev["timestamp"]]
        label = f"{ev['profile_id']} day {ev['mission_day']} {ev['rule_id']}"
        if not ev["expected"]:
            assert not found, f"{label} should NOT fire"
            continue
        assert found, f"{label} should fire"
        a = found[0]
        if "severity" in ev:
            assert a["severity"] == ev["severity"].lower(), label
        for key in ("value", "baseline", "delta"):
            if key in ev:
                assert a[key] == ev[key], f"{label} {key}"
        if "readings" in ev:                       # SLEEP-01: last of the three nights is the alert value
            assert a["value"] == ev["readings"][-1], label


def test_nothing_else_fires_for_astro_01():
    dataset, alerts = evaluate()
    rows = dataset["ASTRO-01"]
    fired = sorted((day_of(rows, a), a["rule_id"]) for a in alerts["ASTRO-01"])
    expected = sorted([(d, "DATA-02") for d in range(1, 8)] + [(20, "HR-01"), (22, "DATA-01"), (26, "SLEEP-01")])
    assert fired == expected


def test_astro_02_is_clean_after_calibration():
    dataset, alerts = evaluate()
    rows = dataset["ASTRO-02"]
    assert sorted((day_of(rows, a), a["rule_id"]) for a in alerts["ASTRO-02"]) == [(d, "DATA-02") for d in range(1, 8)]


def test_day_20_matches_ammaras_example_text():
    _, alerts = evaluate()
    hr = next(a for a in alerts["ASTRO-01"] if a["rule_id"] == "HR-01")
    assert hr["message"] == "Resting heart rate is 78 bpm, 16 bpm above this astronaut's 7-day baseline of 62 bpm."
    assert hr["timestamp"] == "2026-11-04T08:00:00Z"


def test_sleep_01_fires_but_sleep_02_does_not():
    _, alerts = evaluate()
    rule_ids = {a["rule_id"] for a in alerts["ASTRO-01"]}
    assert "SLEEP-01" in rule_ids and "SLEEP-02" not in rule_ids and "HR-02" not in rule_ids


def test_quality_sidecar_is_what_makes_data_01_possible():
    dataset, _ = seed.load_dataset()
    rows = dataset["ASTRO-01"]
    assert rows[21]["spo2_pct"] == 93 and rows[21]["spo2_quality"] == "poor"      # day 22
    assert all(r["spo2_quality"] == "good" for i, r in enumerate(rows) if i != 21)
    assert all(r["spo2_quality"] == "good" for r in dataset["ASTRO-02"])
    assert rows[0]["temp_sensor_location"] == "left_wrist" and rows[0]["temp_device_id"] == "SIM-WEARABLE-01"
    # the five-column CSV alone cannot express quality, so DATA-01 needs the sidecar (as Sofia documents)
    plain = seed.load_rows(SAMPLE / "readings.csv")
    assert "DATA-01" not in {a["rule_id"] for a in rules.evaluate_all(plain)}


def test_dataset_shape_and_import_columns():
    dataset, start = seed.load_dataset()
    assert list(dataset) == ["ASTRO-01", "ASTRO-02"] and start == "2026-10-16"
    for rows in dataset.values():
        assert len(rows) == 30 and rows[0]["timestamp"] == "2026-10-16T08:00:00Z"
        assert rows[-1]["timestamp"] == "2026-11-14T08:00:00Z"
        assert all(28 <= r["body_temp_c"] <= 38 for r in rows)
