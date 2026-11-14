"""Skin-versus-core temperature separation guards (deliverables Section 5).

The engine and schema treat `body_temp_c` as wearable SKIN temperature. These tests
guard that boundary end to end: one stored temperature field, no core value that can
reach a baseline or an alert, skin-labelled TEMP-01 output, and no diagnostic claim
anywhere in the generated alerts.

Unit-level rule behaviour (single spike, +0.5 °C, invalid contact quality) is already
covered by tests/test_rules.py; time-window and sensor-location comparability by
tests/test_baseline.py and tests/test_rule_spec.py.
"""
from __future__ import annotations

import sqlite3

from app import config
from app.db import seed
from app.engine import rules
from tests.helpers import make_series


def temp_cycle(**overrides):
    """Two consecutive +0.6 °C skin readings after a 33.5 °C baseline: TEMP-01 fires."""
    return make_series(9, **{"body_temp_c": [33.5] * 7 + [34.1, 34.1], **overrides})


def test_readings_store_exactly_one_temperature_measurement(client):
    """Skin and core must never share a column.

    Deliberately does NOT assert which tables exist: the spec requires core
    temperature to be stored in its own dedicated table, so adding a
    `core_temperatures` table must not break this test.
    """
    conn = sqlite3.connect(config.db_path())
    try:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(readings)")]
    finally:
        conn.close()
    assert [name for name in columns if name.startswith("body_temp")] == ["body_temp_c"]
    assert not any("core" in name.lower() for name in columns)


def test_an_extra_core_temperature_field_changes_no_baseline_and_no_alert():
    """Even if a caller smuggles a core value into a row, the skin logic must ignore it."""
    skin_only = temp_cycle()
    with_core = [{**row, "core_temp_c": 38.9} for row in skin_only]

    assert rules.evaluate(with_core) == rules.evaluate(skin_only)
    temp = [a for a in rules.evaluate(with_core) if a["rule_id"] == "TEMP-01"]
    assert temp and temp[0]["value"] == 34.1


def test_no_generated_alert_claims_a_diagnosis_or_fever():
    """Runs the real SIMULATED dataset through every rule and checks the wording."""
    dataset, _ = seed.load_dataset()
    alerts = rules.evaluate_all(dataset["ASTRO-01"])
    assert alerts, "the demo dataset should produce alerts to check"

    forbidden = ("fever", "infection", "diagnos")
    for alert in alerts:
        text = alert["message"].lower()
        assert not any(word in text for word in forbidden), f"{alert['rule_id']} claims a diagnosis: {text}"
        assert alert["source"], f"{alert['rule_id']} has no provenance label"


def test_data_quality_alerts_are_separated_from_physiological_ones():
    """DATA-* notices must be visibly a different category, not a health inference."""
    dataset, _ = seed.load_dataset()
    alerts = rules.evaluate_all(dataset["ASTRO-01"])
    for alert in alerts:
        if alert["rule_id"].startswith("DATA"):
            assert alert["category"] in {"data_quality", "setup"}
        else:
            assert alert["category"] == "physiological"
        if alert["rule_id"] == "DATA-01":
            assert alert["value"] is None, "a data-quality notice must not report a measurement"
        if alert["rule_id"] == "DATA-02":
            assert alert["baseline"] is None and alert["baseline_status"] == "not_established"
