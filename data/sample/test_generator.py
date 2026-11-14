"""Regression tests for reproducible SIMULATED engineering fixtures."""

import csv
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from random import Random

from generate_simulated_readings import HEADERS, make_profile, timestamp_for_day, validate


class GeneratorTests(unittest.TestCase):
    def test_schema_and_demo_events(self):
        readings, trace = make_profile("ASTRO-01", date(2026, 10, 16), 30, Random(20261114))
        validate(readings, trace, date(2026, 10, 16), 30, True)
        self.assertEqual(tuple(readings[0]), HEADERS)
        self.assertEqual(readings[19]["heart_rate_bpm"], 78)
        self.assertEqual([readings[d - 1]["sleep_hours"] for d in (24, 25, 26)], [5.4, 5.6, 5.2])
        self.assertEqual(trace[21]["spo2_quality"], "poor")
        self.assertEqual(trace[21]["data_label"], "SIMULATED")

    def test_second_profile_is_clean(self):
        readings, trace = make_profile("ASTRO-02", date(2026, 10, 16), 30, Random(20261115))
        validate(readings, trace, date(2026, 10, 16), 30, False)
        self.assertFalse(any(row["anomaly_id"] for row in trace))
        self.assertTrue(all(6.5 <= row["sleep_hours"] <= 7.5 for row in readings))

    def test_deterministic(self):
        args = ("ASTRO-01", date(2026, 10, 16), 30)
        a = make_profile(*args, Random(20261114))
        b = make_profile(*args, Random(20261114))
        self.assertEqual(a, b)
        self.assertEqual(timestamp_for_day(date(2026, 10, 16), 1), "2026-10-16T08:00:00Z")

    def test_final_csv_header(self):
        with Path(__file__).with_name("readings.csv").open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            self.assertEqual(tuple(reader.fieldnames), HEADERS)
            self.assertEqual(len(list(reader)), 30)


if __name__ == "__main__":
    unittest.main()
