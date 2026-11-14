"""Local RAG module for Astro-Health Companion (Ammara's 9-source library & v2 rules).

Exposes the contract required by backend/app/services/rag_adapter.py:
    ask(question: str, alert: dict | None) -> dict
    retrieval_only(question: str, alert: dict | None) -> dict

Both functions return:
    {
        "answer": str,
        "mode": "llm" | "retrieval_only",
        "citations": [{"title": str, "source": str, "url": str, "excerpt": str}],
    }
"""
from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

NOT_FOUND = "I cannot answer that from my sources."

# Ammara's Curated Scientific Library (Section 5, S1-S9, 13 Nov 2026).
# DOIs are used as stable links. None of these sources establishes a clinical numeric cut-off;
# all numeric triggers are prototype workflow rules compared against personal baselines.
DEFAULT_CORPUS: list[dict[str, Any]] = [
    {
        "id": "S1",
        "metrics": ["heart_rate_bpm", "spo2_pct", "sleep_hours", "body_temp_c"],
        "rules": [],
        "keywords": [
            "s1", "winkler", "physiological", "limitations", "long-term", "spaceflight",
            "hazard", "deconditioning", "microgravity", "adaptation", "overview",
        ],
        "title": (
            "S1: Winkler LH. Human physiological limitations to long-term spaceflight "
            "and living in space (2023)"
        ),
        "source": "Aerosp Med Hum Perform. 2023;94(6):444-456 (PMID 37194175)",
        "url": "https://doi.org/10.3357/AMHP.6190.2023",
        "excerpt": (
            "Broad multi-system hazard context for long-duration spaceflight across cardiovascular, "
            "respiratory, musculoskeletal, neurovestibular, and behavioural domains. Limitation: "
            "single-author narrative review; routine wearables cannot detect every physiological change."
        ),
    },
    {
        "id": "S2",
        "metrics": ["heart_rate_bpm"],
        "rules": ["HR-01", "hr_above_baseline"],
        "keywords": [
            "s2", "tomsia", "heart", "rate", "bpm", "hrv", "variability", "cardiovascular",
            "resting", "baseline", "autonomic", "adaptation", "pulse", "hr-01",
        ],
        "title": (
            "S2: Tomsia M, Cieśla J, Śmieszek J, et al. Long-term space missions' effects on the "
            "human organism: what we do know and what requires further research (2024)"
        ),
        "source": "Front Physiol. 2024;15:1284644",
        "url": "https://doi.org/10.3389/fphys.2024.1284644",
        "excerpt": (
            "Documents multi-system effects of long-duration spaceflight and highlights resting "
            "heart-rate and heart-rate variability shifts as markers of autonomic adaptation and "
            "cardiovascular load. Limitation: mixes astronaut, ground-analog, and animal evidence."
        ),
    },
    {
        "id": "S3",
        "metrics": ["heart_rate_bpm"],
        "rules": ["HR-02", "DATA-02", "hr_absolute_high"],
        "keywords": [
            "s3", "russell", "decision", "support", "cdss", "earth-independent", "autonomous",
            "persistent", "deviation", "baseline", "calibration", "hr-02", "data-02", "trend",
        ],
        "title": (
            "S3: Russell BK, Burian BK, Hilmers DC, et al. The value of a spaceflight clinical "
            "decision support system for Earth-independent medical operations (2023)"
        ),
        "source": "npj Microgravity. 2023;9:46 (PMC10284846)",
        "url": "https://doi.org/10.1038/s41526-023-00284-1",
        "excerpt": (
            "Supports onboard clinical decision-support workflows when communication delays "
            "require crew autonomy and structured trend review before escalating to flight medicine. "
            "Limitation: conceptual/operational evidence; does not prove this prototype is clinically "
            "effective or safe."
        ),
    },
    {
        "id": "S4",
        "metrics": ["heart_rate_bpm", "spo2_pct", "body_temp_c", "skin_temp_c"],
        "rules": ["HR-01", "SPO2-01", "TEMP-01", "DATA-01", "DATA-02", "spo2_low", "temp_high"],
        "keywords": [
            "s4", "gupta", "ghosh", "wearable", "wearables", "sensor", "monitoring", "spo2",
            "oxygen", "saturation", "skin", "temperature", "signal", "quality", "contact",
            "artifact", "fit", "spo2-01", "temp-01", "data-01", "baseline",
        ],
        "title": (
            "S4: Gupta R, Ghosh PS. Advancements in health monitoring technologies for astronauts "
            "in deep space missions: a review (2025)"
        ),
        "source": "Life Sci Space Res. 2025;47:190-196 (PMID 41136019)",
        "url": "https://doi.org/10.1016/j.lssr.2025.06.011",
        "excerpt": (
            "Reviews wearable physiological biosensors (heart rate, SpO2, peripheral skin temperature) "
            "and longitudinal baseline tracking for deep-space missions, emphasizing that sensor "
            "placement, contact quality, and signal artifacts must be verified before interpreting "
            "deviations. Limitation: sensor accuracy and flight validation remain open; abstract-level "
            "access only."
        ),
    },
    {
        "id": "S5",
        "metrics": ["heart_rate_bpm"],
        "rules": ["HR-02", "hr_absolute_high"],
        "keywords": [
            "s5", "levin", "steller", "eimo", "earth", "independent", "medical", "operations",
            "protocol", "escalation", "persistent", "ground", "officer", "hr-02",
        ],
        "title": (
            "S5: Levin DR, Steller J, Anderson A, et al. Enabling human space exploration missions "
            "through progressively Earth independent medical operations (EIMO) (2023)"
        ),
        "source": "IEEE Open J Eng Med Biol. 2023;4:162-167 (PMC10810302)",
        "url": "https://doi.org/10.1109/OJEMB.2023.3255513",
        "excerpt": (
            "Defines the progressive Earth-Independent Medical Operations (EIMO) framework for "
            "crew self-monitoring, repeat verification of persistent vital-sign deviations, and "
            "criteria for contacting ground or the crew medical officer. Limitation: operational "
            "framework, not a clinical trial of a monitoring app."
        ),
    },
    {
        "id": "S6",
        "metrics": ["body_temp_c", "skin_temp_c"],
        "rules": ["TEMP-01", "temp_high"],
        "keywords": [
            "s6", "marchal", "chouker", "immune", "temperature", "skin", "core", "stressors",
            "thermoregulation", "temp-01", "celsius",
        ],
        "title": (
            "S6: Marchal S, Choukér A, Bereiter-Hahn J, et al. Challenges for the human immune "
            "system after leaving Earth (2024)"
        ),
        "source": "npj Microgravity. 2024;10 (published 18 Nov 2024)",
        "url": "https://doi.org/10.1038/s41526-024-00446-9",
        "excerpt": (
            "Examines spaceflight stressors and immune regulation in microgravity. Clinical boundary: "
            "immune outcomes require dedicated laboratory assays; wearable skin-temperature trends "
            "are not core-temperature measurements and cannot diagnose fever, infection, or immune "
            "dysfunction."
        ),
    },
    {
        "id": "S7",
        "metrics": ["sleep_hours"],
        "rules": ["SLEEP-01", "SLEEP-02", "sleep_low_streak"],
        "keywords": [
            "s7", "barbour", "sleep", "nights", "hours", "fatigue", "circadian", "isolation",
            "stress", "mood", "workload", "schedule", "countermeasures", "biopsychosocial",
            "sleep-01", "sleep-02",
        ],
        "title": (
            "S7: Barbour BN, Twardowska K, Favero N, et al. Biopsychosocial health considerations "
            "for astronauts in long-duration spaceflight: a narrative review (2025)"
        ),
        "source": "Wilderness Environ Med. 2025;36(1_suppl):123S-137S (PMID 39470395)",
        "url": "https://doi.org/10.1177/10806032241289106",
        "excerpt": (
            "Reviews isolation, sleep loss, circadian misalignment, workload, mood, and team factors "
            "in long-duration missions, supporting schedule, environment, and sleep countermeasure "
            "reviews after multi-night sleep restriction. Limitation: narrative framework, not a "
            "validated predictive model; sleep duration alone does not diagnose a behavioural-health "
            "or psychiatric condition."
        ),
    },
    {
        "id": "S8",
        "metrics": [],
        "rules": [],
        "keywords": [
            "s8", "narici", "radiation", "cosmic", "shielding", "dosimetry", "exposure",
        ],
        "title": (
            "S8: Narici L, Baiocco G, Cenci G, et al. Radiation risk mitigation in human space "
            "exploration: a primer, a vision, and the state of the art (2026)"
        ),
        "source": "Eur Phys J Plus. 2026;141:100",
        "url": "https://doi.org/10.1140/epjp/s13360-025-07199-8",
        "excerpt": (
            "Provides space radiation risk context only. Physical radiation exposure and biological "
            "risk are distinct; wearable vital-sign monitors do not measure radiation dose or "
            "diagnose radiation injury."
        ),
    },
    {
        "id": "S9",
        "metrics": [],
        "rules": [],
        "keywords": [
            "s9", "roberts", "musculoskeletal", "bone", "muscle", "tendon", "exercise",
            "atrophy", "countermeasures", "resistive",
        ],
        "title": (
            "S9: Roberts BM, Deane CS, Szewczyk NJ, et al. Musculoskeletal responses to "
            "spaceflight: mechanisms, countermeasures, and key gaps (2025)"
        ),
        "source": "Am J Physiol Cell Physiol. 2025;329(6):C1985-C1993",
        "url": "https://doi.org/10.1152/ajpcell.00649.2025",
        "excerpt": (
            "Summarizes bone, muscle, and tendon deconditioning mechanisms and exercise "
            "countermeasures in microgravity. Clinical boundary: routine wearable telemetry and "
            "exercise logs do not measure bone mineral density or muscle mass."
        ),
    },
]

# Exact rule -> source ID mapping from Section 3 of Ammara's deliverables pack
RULE_SOURCE_MAP: dict[str, list[str]] = {
    "HR-01": ["S2", "S4"],
    "HR-02": ["S3", "S5"],
    "SPO2-01": ["S4"],
    "SLEEP-01": ["S7"],
    "SLEEP-02": ["S7"],
    "TEMP-01": ["S4", "S6"],
    "DATA-01": ["S4"],
    "DATA-02": ["S3", "S4"],
    # Legacy v1 rule compatibility
    "hr_above_baseline": ["S2", "S4"],
    "hr_absolute_high": ["S3", "S5"],
    "spo2_low": ["S4"],
    "sleep_low_streak": ["S7"],
    "temp_high": ["S4", "S6"],
}

# Clinical boundary statements per rule/metric (Sections 2 & 2.1 of Ammara's deliverables pack)
CLINICAL_BOUNDARIES: dict[str, str] = {
    "HR-01": (
        "Resting heart rate deviation does not infer arrhythmia, cardiovascular disease, "
        "or immune dysfunction."
    ),
    "HR-02": (
        "Persistent resting heart rate deviation is an operational trend flag and does not "
        "diagnose arrhythmia or cardiovascular disease."
    ),
    "SPO2-01": (
        "Spot SpO2 deviation is not a diagnosis of hypoxia or cardiopulmonary disease; "
        "signal quality and sensor fit must be confirmed first."
    ),
    "SLEEP-01": (
        "Sleep duration alone does not diagnose a behavioural-health or psychiatric condition."
    ),
    "SLEEP-02": (
        "Sleep deviation below personal baseline does not diagnose a behavioural-health "
        "or psychiatric condition."
    ),
    "TEMP-01": (
        "Wearable skin temperature is not a core-temperature measurement and cannot "
        "independently establish elevated core temperature or infer fever, infection, "
        "or immune dysfunction."
    ),
    "DATA-01": (
        "This is a data-quality notice (missing, stale, or poor-quality signal), not a "
        "physiological alert; infer no health event."
    ),
    "DATA-02": (
        "This is a baseline-calibration notice (fewer than 7 valid comparable readings "
        "and no preflight baseline) to prevent false precision; infer no health event."
    ),
}

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "did", "do", "does",
    "for", "from", "had", "has", "have", "how", "i", "in", "is", "it", "its",
    "me", "my", "of", "on", "or", "should", "so", "that", "the", "their", "them",
    "there", "these", "this", "to", "was", "what", "when", "where", "which",
    "who", "why", "will", "with", "would", "you", "your", "flagged", "alert",
    "mean", "explain", "tell", "about", "happened", "research", "say", "says",
}


def _ensure_default_meta() -> None:
    """Ensures rag/index/meta.json exists in the repo folder even on a fresh git clone."""
    meta_path = Path(__file__).resolve().parent / "index" / "meta.json"
    if not meta_path.is_file():
        try:
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(
                json.dumps({"documents_indexed": len(DEFAULT_CORPUS)}, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass


_ensure_default_meta()


def _load_corpus() -> list[dict[str, Any]]:
    """Loads custom corpus from RAG_INDEX_DIR/corpus.json if present, else DEFAULT_CORPUS."""
    repo_root = Path(__file__).resolve().parents[1]
    index_dir = Path(os.environ.get("RAG_INDEX_DIR", repo_root / "rag" / "index"))
    corpus_file = index_dir / "corpus.json"
    if corpus_file.is_file():
        try:
            data = json.loads(corpus_file.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return DEFAULT_CORPUS


def _tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9_-]+", text.lower()))
    return {t for t in tokens if len(t) > 1 and t not in _STOPWORDS}


def _to_citation(doc: dict[str, Any]) -> dict[str, str]:
    return {
        "title": str(doc.get("title", "")),
        "source": str(doc.get("source", "")),
        "url": str(doc.get("url", "")),
        "excerpt": str(doc.get("excerpt", "")),
    }


def _retrieve(question: str, alert: dict | None, top_k: int = 2) -> list[dict[str, str]]:
    corpus = _load_corpus()
    by_id = {d.get("id"): d for d in corpus if d.get("id")}
    q_tokens = _tokenize(question or "")

    # 1. If an alert is supplied and maps to specific Ammara sources (S1-S9), prioritize those exact sources
    if alert is not None:
        rule_id = alert.get("rule_id") or ""
        mapped_ids = RULE_SOURCE_MAP.get(rule_id, [])
        mapped_docs = [by_id[sid] for sid in mapped_ids if sid in by_id]
        if mapped_docs:
            return [_to_citation(d) for d in mapped_docs[:top_k]]

    # 2. Otherwise score corpus documents by rule/metric alignment and lexical overlap
    alert_metric = (alert or {}).get("metric")
    alert_rule = (alert or {}).get("rule_id")
    alert_tokens = _tokenize(f"{(alert or {}).get('rule', '')} {(alert or {}).get('message', '')}")

    scored: list[tuple[float, dict[str, Any]]] = []
    for doc in corpus:
        score = 0.0
        doc_keywords = {k.lower() for k in doc.get("keywords", [])}
        doc_text_tokens = _tokenize(f"{doc.get('title', '')} {doc.get('excerpt', '')}") | doc_keywords

        if alert is not None:
            if alert_rule and alert_rule in doc.get("rules", []):
                score += 6.0
            if alert_metric and alert_metric in doc.get("metrics", []):
                score += 4.0
            score += 0.5 * len(alert_tokens & doc_text_tokens)

        keyword_hits = q_tokens & doc_keywords
        text_hits = q_tokens & doc_text_tokens
        score += 3.0 * len(keyword_hits) + 1.0 * len(text_hits)

        if score > 0:
            scored.append((score, doc))

    # When no alert is given, require at least one domain keyword match so unsupported questions
    # (e.g., "What is the weather on Mars?") honestly return no citations.
    if alert is None:
        all_domain_keywords = {k.lower() for doc in corpus for k in doc.get("keywords", [])}
        if not (q_tokens & all_domain_keywords):
            return []

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [doc for _, doc in scored[:top_k]]

    if not selected and alert is not None and corpus:
        selected = corpus[:top_k]

    return [_to_citation(d) for d in selected]


def _format_retrieval_answer(question: str, alert: dict | None, citations: list[dict[str, str]]) -> str:
    refs = "".join(f"[{i}]" for i in range(1, len(citations) + 1))
    excerpts = " ".join(f"[{i}] {c['excerpt']}" for i, c in enumerate(citations, start=1))

    if alert is not None:
        severity = (alert.get("severity") or "notice").upper()
        rule_id = alert.get("rule_id") or ""
        rule_name = alert.get("rule") or "Prototype monitoring rule"
        msg = alert.get("message") or f"{alert.get('metric')} triggered a notice."
        step = alert.get("next_step") or "Re-measure and follow mission medical procedure."
        boundary = CLINICAL_BOUNDARIES.get(
            rule_id,
            "All numeric triggers are prototype workflow rules, not clinical thresholds.",
        )
        rule_label = f"Rule {rule_id} ({rule_name}) fired." if rule_id else f"Rule '{rule_name}' fired."
        return (
            f"{severity} - {msg} {rule_label} "
            f"Scientific library context {refs}: {excerpts} "
            f"Clinical boundary: {boundary} "
            f"Suggested next step: {step}. "
            f"This is a monitoring alert, not a diagnosis."
        )

    return (
        f"From the local scientific library {refs}: {excerpts} "
        f"Note: Curated sources provide spaceflight physiological context only and do not "
        f"establish diagnostic thresholds."
    )


def _try_ollama_generate(question: str, alert: dict | None, citations: list[dict[str, str]]) -> str | None:
    """Calls local Ollama server if reachable and a model is available; returns None on any error."""
    base_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.environ.get("OLLAMA_MODEL", "").strip()

    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=1.0) as resp:
            if resp.status != 200:
                return None
            tags_data = json.loads(resp.read().decode("utf-8"))
            models = [m.get("name") for m in tags_data.get("models", []) if m.get("name")]
            if not model:
                if not models:
                    return None
                model = models[0]
            elif model not in models and f"{model}:latest" not in models:
                return None
    except Exception:
        return None

    context_blocks = "\n".join(
        f"[{i}] {c['title']} — {c['source']} ({c['url']}): {c['excerpt']}"
        for i, c in enumerate(citations, start=1)
    )
    alert_block = ""
    if alert is not None:
        rule_id = alert.get("rule_id") or ""
        boundary = CLINICAL_BOUNDARIES.get(rule_id, "")
        alert_block = (
            f"Alert Severity: {(alert.get('severity') or '').upper()}\n"
            f"Rule ID & Name: {rule_id} ({alert.get('rule')})\n"
            f"Alert Category: {alert.get('category', 'physiological')}\n"
            f"Alert Explanation: {alert.get('message')}\n"
            f"Suggested Next Step: {alert.get('next_step')}\n"
            f"Clinical Boundary: {boundary}\n\n"
        )

    prompt = (
        "You are an offline astronaut health decision-support assistant. "
        "Follow these strict rules:\n"
        "1. Use ONLY the provided scientific sources and alert details.\n"
        "2. Cite sources inline as [1], [2].\n"
        "3. State the rule ID, plain-language explanation, and suggested next step.\n"
        "4. NEVER infer a medical diagnosis, fever, infection, hypoxia, arrhythmia, or immune/psychiatric "
        "condition from wearable indicators or skin temperature. Skin temperature is not core temperature.\n"
        "5. If the alert is DATA-01 or DATA-02, state clearly that it is a data-quality or baseline-setup notice "
        "and infer no health event.\n"
        "6. End with: 'This is a monitoring alert, not a diagnosis.'\n\n"
        f"{alert_block}"
        f"Sources:\n{context_blocks}\n\n"
        f"Question: {question}\n"
        "Answer:"
    )

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    timeout = max(1.0, float(os.environ.get("ASK_TIMEOUT_SECONDS", "20")) - 2.0)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            body = json.loads(resp.read().decode("utf-8"))
            text = (body.get("response") or "").strip()
            return text if text else None
    except Exception:
        return None


def retrieval_only(question: str, alert: dict | None = None) -> dict[str, Any]:
    """Retrieves relevant citations from Ammara's 9 sources without calling the language model."""
    citations = _retrieve(question, alert)
    if not citations:
        return {
            "answer": NOT_FOUND,
            "mode": "retrieval_only",
            "citations": [],
        }
    return {
        "answer": _format_retrieval_answer(question, alert, citations),
        "mode": "retrieval_only",
        "citations": citations,
    }


def ask(question: str, alert: dict | None = None) -> dict[str, Any]:
    """Answers a question grounded in S1-S9, using Ollama when available or retrieval_only otherwise."""
    citations = _retrieve(question, alert)
    if not citations:
        return {
            "answer": NOT_FOUND,
            "mode": "retrieval_only",
            "citations": [],
        }

    llm_answer = _try_ollama_generate(question, alert, citations)
    if llm_answer:
        return {
            "answer": llm_answer,
            "mode": "llm",
            "citations": citations,
        }

    return {
        "answer": _format_retrieval_answer(question, alert, citations),
        "mode": "retrieval_only",
        "citations": citations,
    }
