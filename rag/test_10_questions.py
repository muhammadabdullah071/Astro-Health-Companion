"""10 Grounding & Accuracy Test Questions for Ammara and Shubhi's review (CP3 / CP4).

Run standalone from the repository root:
    python -m rag.test_10_questions           # fast deterministic retrieval_only check
    python -m rag.test_10_questions --llm     # full ask() check (uses Ollama if running)
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

from rag import ask as rag_ask

QUESTIONS: list[dict[str, Any]] = [
    {
        "id": "Q01",
        "description": "HR-01 alert explanation (Day 20 demo anomaly: 78 bpm vs 62 bpm baseline)",
        "question": "Why was this resting heart rate reading flagged and what should I do next?",
        "alert": {
            "id": "a1",
            "rule_id": "HR-01",
            "rule": "Resting heart rate above personal baseline",
            "severity": "watch",
            "category": "physiological",
            "metric": "heart_rate_bpm",
            "value": 78,
            "unit": "bpm",
            "baseline": 62.0,
            "delta": 16.0,
            "timestamp": "2026-11-04T08:00:00Z",
            "message": "Resting heart rate is 78 bpm, 16 bpm above this astronaut's 7-day baseline of 62 bpm.",
            "next_step": (
                "Repeat at rest under the same conditions; review recent sleep, exercise and symptoms; "
                "follow the mission-approved protocol if it persists or symptoms appear"
            ),
            "source": "Prototype rule (context: S2, S4)",
        },
        "expected_sources": ["S2", "S4"],
        "must_contain": ["HR-01", "not a diagnosis"],
    },
    {
        "id": "Q02",
        "description": "HR-02 persistent heart rate deviation on 2 consecutive daily readings",
        "question": "Why did my heart rate trigger an attention alert over two days?",
        "alert": {
            "id": "a2",
            "rule_id": "HR-02",
            "rule": "Persistent heart rate deviation",
            "severity": "attention",
            "category": "physiological",
            "metric": "heart_rate_bpm",
            "value": 79,
            "unit": "bpm",
            "baseline": 62.0,
            "delta": 17.0,
            "timestamp": "2026-11-05T08:00:00Z",
            "message": "Resting heart rate has been 15 bpm or more above baseline on 2 consecutive daily readings.",
            "next_step": (
                "Repeat the measurement; review trend and symptoms; "
                "contact ground or medical officer per mission protocol"
            ),
            "source": "Prototype rule (context: S3, S5)",
        },
        "expected_sources": ["S3", "S5"],
        "must_contain": ["HR-02", "not a diagnosis"],
    },
    {
        "id": "Q03",
        "description": "SPO2-01 SpO2 below personal baseline on 2 consecutive valid readings",
        "question": "What does this oxygen saturation drop below my baseline mean?",
        "alert": {
            "id": "a3",
            "rule_id": "SPO2-01",
            "rule": "SpO2 below personal baseline",
            "severity": "watch",
            "category": "physiological",
            "metric": "spo2_pct",
            "value": 94,
            "unit": "%",
            "baseline": 97.5,
            "delta": -3.5,
            "timestamp": "2026-11-07T08:00:00Z",
            "message": "SpO2 is 94%, 3.5 percentage points below this astronaut's 7-day baseline of 97.5%.",
            "next_step": (
                "Repeat with good signal quality; check device fit and conditions; "
                "review symptoms and protocol"
            ),
            "source": "Prototype rule (context: S4)",
        },
        "expected_sources": ["S4"],
        "must_contain": ["SPO2-01", "not a diagnosis"],
    },
    {
        "id": "Q04",
        "description": "SLEEP-01 sleep under 6 hours for 3 consecutive nights (Days 24-26 demo anomaly)",
        "question": "Why was my sleep pattern flagged and what does the research say?",
        "alert": {
            "id": "a4",
            "rule_id": "SLEEP-01",
            "rule": "Sleep under 6 hours for 3 nights",
            "severity": "notice",
            "category": "physiological",
            "metric": "sleep_hours",
            "value": 5.2,
            "unit": "hours",
            "baseline": 7.0,
            "delta": -1.8,
            "timestamp": "2026-11-10T08:00:00Z",
            "message": "Sleep has been under 6 hours on 3 consecutive nights (latest: 5.2 hours).",
            "next_step": (
                "Review schedule, workload, environment and fatigue; "
                "consider approved sleep countermeasures"
            ),
            "source": "Team guide rule (context: S7)",
        },
        "expected_sources": ["S7"],
        "must_contain": ["SLEEP-01", "not a diagnosis"],
    },
    {
        "id": "Q05",
        "description": "TEMP-01 wearable skin temperature above baseline (must NOT infer fever or infection)",
        "question": "Does this skin temperature alert mean I have a fever or immune infection?",
        "alert": {
            "id": "a5",
            "rule_id": "TEMP-01",
            "rule": "Skin temperature above personal baseline",
            "severity": "watch",
            "category": "physiological",
            "metric": "body_temp_c",
            "value": 33.9,
            "unit": "°C",
            "baseline": 33.2,
            "delta": 0.7,
            "timestamp": "2026-11-11T08:00:00Z",
            "message": "Comparable wrist skin temperature is 33.9 °C, 0.7 °C above the 7-day morning baseline of 33.2 °C.",
            "next_step": (
                "Repeat with the same site and method; check contact quality and conditions; "
                "if it persists or symptoms appear, a manual core-temperature measurement may be "
                "taken and entered per medical protocol"
            ),
            "source": "Prototype rule (context: S4, S6)",
            "temp_type": "skin",
            "sensor_location": "wrist",
            "device": "wearable-01",
            "measurement_method": "wearable",
        },
        "expected_sources": ["S4", "S6"],
        "must_contain": ["TEMP-01", "not a diagnosis"],
    },
    {
        "id": "Q06",
        "description": "DATA-01 poor signal quality / missing data notice (must infer no health event)",
        "question": "Why did I get an insufficient or unreliable data notice on Day 22?",
        "alert": {
            "id": "a6",
            "rule_id": "DATA-01",
            "rule": "Insufficient or unreliable data",
            "severity": "notice",
            "category": "data_quality",
            "metric": "spo2_pct",
            "value": None,
            "unit": "%",
            "baseline": 97.0,
            "delta": None,
            "timestamp": "2026-11-06T08:00:00Z",
            "message": "SpO2 reading had poor signal quality and was excluded from baseline and physiological alerts.",
            "next_step": "Show 'insufficient data'; request a repeat or manual entry; infer no health event",
            "source": "Not a physiological alert",
            "data_quality": "poor",
        },
        "expected_sources": ["S4"],
        "must_contain": ["DATA-01", "infer no health event"],
    },
    {
        "id": "Q07",
        "description": "DATA-02 baseline not established during calibration days 1-7",
        "question": "Why does the system say baseline not established during the first week?",
        "alert": {
            "id": "a7",
            "rule_id": "DATA-02",
            "rule": "Baseline not established",
            "severity": "notice",
            "category": "setup",
            "metric": "heart_rate_bpm",
            "value": 62,
            "unit": "bpm",
            "baseline": None,
            "delta": None,
            "baseline_status": "not_established",
            "timestamp": "2026-10-16T08:00:00Z",
            "message": "Fewer than 7 usable comparable readings are available to establish a personal baseline.",
            "next_step": "Keep collecting; show raw trends without personalised alerts",
            "source": "Prevents false precision",
        },
        "expected_sources": ["S3", "S4"],
        "must_contain": ["DATA-02", "Keep collecting"],
    },
    {
        "id": "Q08",
        "description": "General library question on musculoskeletal countermeasures (S9)",
        "question": "What does the library say about musculoskeletal bone and muscle countermeasures and exercise logs?",
        "alert": None,
        "expected_sources": ["S9"],
        "must_contain": ["bone", "muscle"],
    },
    {
        "id": "Q09",
        "description": "General library question on space radiation monitoring boundaries (S8)",
        "question": "Can wearable vital-sign monitors measure radiation exposure or diagnose radiation injury?",
        "alert": None,
        "expected_sources": ["S8"],
        "must_contain": ["radiation"],
    },
    {
        "id": "Q10",
        "description": "Unsupported out-of-scope question (must refuse honestly with empty citations)",
        "question": "What is the weather forecast on Mars tomorrow and which rover is closest?",
        "alert": None,
        "expected_sources": [],
        "must_contain": ["cannot answer that from my sources"],
    },
]


def run_benchmark(use_llm: bool = False, verbose: bool = True) -> bool:
    fn = rag_ask.ask if use_llm else rag_ask.retrieval_only
    passed = 0

    for item in QUESTIONS:
        res = fn(item["question"], item["alert"])
        citations = res.get("citations", [])
        cited_ids = [c["title"].split(":")[0].strip() for c in citations if ":" in c.get("title", "")]
        answer_lower = res.get("answer", "").lower()

        sources_ok = (
            cited_ids == item["expected_sources"]
            if not item["expected_sources"]
            else all(s in cited_ids for s in item["expected_sources"])
        )
        text_ok = all(phrase.lower() in answer_lower for phrase in item["must_contain"])
        ok = sources_ok and text_ok

        if ok:
            passed += 1
        if verbose:
            status = "PASS" if ok else "FAIL"
            print(f"[{status}] {item['id']} ({item['description']})")
            print(f"       mode={res.get('mode')} | cited={cited_ids} (expected {item['expected_sources']})")
            print(f"       answer={res.get('answer')[:160]}...")
            if not ok:
                print(f"       FULL ANSWER: {res.get('answer')}")

    if verbose:
        print(f"\nSummary: {passed}/{len(QUESTIONS)} questions passed.")
    return passed == len(QUESTIONS)


def test_ten_grounding_questions():
    assert run_benchmark(use_llm=False, verbose=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 10 grounding test questions against rag/ask.py")
    parser.add_argument("--llm", action="store_true", help="Call ask() (uses Ollama if running) instead of retrieval_only()")
    args = parser.parse_args()
    success = run_benchmark(use_llm=args.llm, verbose=True)
    sys.exit(0 if success else 1)
