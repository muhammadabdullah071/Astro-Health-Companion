"""Ammara's demo scenario on the placeholder sample data: day 20 HR-01, days 24 to 26 SLEEP-01."""
from collections import defaultdict

from app.db import seed
from app.engine import rules


def by_day():
    rows = seed.load_rows()
    out = defaultdict(list)
    for a in rules.evaluate_all(rows):
        day = [r["timestamp"] for r in rows].index(a["timestamp"]) + 1
        out[day].append(a["rule_id"])
    return rows, out


def test_dataset_is_26_days_ending_on_day_26():
    rows, _ = by_day()
    assert len(rows) == 26


def test_exactly_the_expected_alerts_fire():
    _, out = by_day()
    assert out[20] == ["HR-01"]
    assert out[26] == ["SLEEP-01"]
    assert sorted(d for d in out if d not in (20, 26)) == list(range(1, 8))
    for day in range(1, 8):
        assert out[day] == ["DATA-02"]          # calibration window


def test_nothing_else_fires():
    _, out = by_day()
    fired = {r for day in out.values() for r in day}
    assert fired == {"HR-01", "SLEEP-01", "DATA-02"}   # no HR-02, SLEEP-02, SPO2-01, TEMP-01, DATA-01


def test_day_20_matches_ammaras_example():
    rows = seed.load_rows()
    a = next(x for x in rules.evaluate_all(rows) if x["rule_id"] == "HR-01")
    assert a["value"] == 78 and 61 <= a["baseline"] <= 63
    assert round(a["delta"]) == 16
    assert a["message"].startswith("Resting heart rate is 78 bpm, 16 bpm above this astronaut's 7-day baseline of 6")
