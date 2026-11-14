"""CLI-level regression tests for Sofia's SIMULATED generator (data/sample/).

`data/sample/test_generator.py` already unit-tests `make_profile()` and `validate()`
in place. This file covers what that cannot: the command a teammate actually runs,
the files it writes, byte-level reproducibility between runs, and that its output
still imports through the backend's own loader.

Output goes to a temporary folder; no second copy of the dataset is added to the repo.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

SAMPLE = Path(__file__).resolve().parents[2] / "data" / "sample"
GENERATOR = SAMPLE / "generate_simulated_readings.py"
DELIVERABLES = (
    "readings.csv",
    "readings.json",
    "readings_profile_02.csv",
    "readings_profile_02.json",
    "traceability.csv",
    "manifest.json",
    "expected_alerts.json",
)


def run_generator(out: Path, *extra: str):
    return subprocess.run(
        [sys.executable, str(GENERATOR), "--out", str(out), *extra],
        capture_output=True,
        text=True,
    )


def read_rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    out = tmp_path_factory.mktemp("generated")
    result = run_generator(out)
    assert result.returncode == 0, f"generator failed:\n{result.stdout}\n{result.stderr}"
    return out


def test_cli_runs_and_writes_every_deliverable(generated):
    for name in DELIVERABLES:
        assert (generated / name).is_file(), f"missing generator output: {name}"


def test_same_seed_reproduces_identical_files(generated, tmp_path):
    rerun = tmp_path / "same_seed"
    assert run_generator(rerun).returncode == 0
    for name in ("readings.csv", "readings_profile_02.csv", "traceability.csv", "manifest.json",
                 "expected_alerts.json"):
        assert (rerun / name).read_bytes() == (generated / name).read_bytes(), f"{name} is not reproducible"


def test_a_different_seed_keeps_the_planted_scenarios(tmp_path):
    out = tmp_path / "seed_7"
    assert run_generator(out, "--seed", "7").returncode == 0
    rows = read_rows(out / "readings.csv")
    assert float(rows[19]["heart_rate_bpm"]) == 78
    assert float(rows[21]["spo2_pct"]) == 93
    assert [float(row["sleep_hours"]) for row in rows[23:26]] == [5.4, 5.6, 5.2]


def test_too_short_a_history_is_refused(tmp_path):
    result = run_generator(tmp_path / "short", "--days", "10")
    assert result.returncode != 0
    assert "At least 26 days" in result.stderr


def test_shorter_run_writes_data_but_no_expected_events_file(tmp_path):
    out = tmp_path / "days_26"
    assert run_generator(out, "--days", "26").returncode == 0
    assert len(read_rows(out / "readings.csv")) == 26
    assert not (out / "expected_alerts.json").exists()


def test_single_profile_run_writes_only_one_profile(tmp_path):
    out = tmp_path / "one_profile"
    assert run_generator(out, "--profiles", "1").returncode == 0
    assert (out / "readings.csv").is_file()
    assert not (out / "readings_profile_02.csv").exists()


def test_expected_events_line_up_with_the_generated_timestamps(generated):
    """The fixture's mission days must still match the CSV it describes."""
    events = json.loads((generated / "expected_alerts.json").read_text(encoding="utf-8"))["expected_events"]
    rows = read_rows(generated / "readings.csv")
    primary = [event for event in events if event["profile_id"] == "ASTRO-01"]
    assert primary
    for event in primary:
        assert event["timestamp"] == rows[event["mission_day"] - 1]["timestamp"], event["rule_id"]


def test_generated_csv_still_imports_through_the_backend_loader(generated):
    """Cross-component guard: the generator and the importer must not drift apart."""
    from app.db import seed

    loaded = seed.load_rows(generated / "readings.csv")
    assert len(loaded) == 30
    assert all(isinstance(row["heart_rate_bpm"], float) for row in loaded)
    assert loaded == sorted(loaded, key=lambda row: row["timestamp"])
