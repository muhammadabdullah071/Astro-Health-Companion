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

Also provides PC hardware capability detection, model tier selection, and direct model
downloading (GGUF into ./models/ or via Ollama):
    python -m rag.ask --check
    python -m rag.ask --configure
    python -m rag.ask --download auto
"""
from __future__ import annotations

import argparse
import ctypes
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

NOT_FOUND = "I cannot answer that from my sources."

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "models"

# Curated local LLM catalog mapped to PC hardware capability tiers.
# Uses public Apache-2.0 / open-weights GGUF files from Hugging Face and official Ollama tags.
MODEL_CATALOG: dict[str, dict[str, Any]] = {
    "nano": {
        "tier": "nano",
        "label": "Nano (~0.5B parameters)",
        "description": "Ultra-lightweight model for basic CPUs and low free RAM (>= 2.0 GB free).",
        "min_ram_gb": 2.0,
        "ollama_model": "qwen2.5:0.5b",
        "gguf_filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "gguf_size_mb": 398,
        "gguf_url": (
            "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/"
            "qwen2.5-0.5b-instruct-q4_k_m.gguf"
        ),
    },
    "small": {
        "tier": "small",
        "label": "Small (~1.5B parameters)",
        "description": "Balanced speed and accuracy for standard laptops (>= 4.5 GB free RAM).",
        "min_ram_gb": 4.5,
        "ollama_model": "qwen2.5:1.5b",
        "gguf_filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "gguf_size_mb": 1120,
        "gguf_url": (
            "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/"
            "qwen2.5-1.5b-instruct-q4_k_m.gguf"
        ),
    },
    "standard": {
        "tier": "standard",
        "label": "Standard (~3B parameters)",
        "description": "Higher quality reasoning for PCs with >= 8.0 GB free RAM or >= 4 GB GPU VRAM.",
        "min_ram_gb": 7.5,
        "ollama_model": "llama3.2:3b",
        "gguf_filename": "qwen2.5-3b-instruct-q4_k_m.gguf",
        "gguf_size_mb": 2050,
        "gguf_url": (
            "https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/"
            "qwen2.5-3b-instruct-q4_k_m.gguf"
        ),
    },
}

DEFAULT_LLM_CONFIG: dict[str, str] = {
    "backend": "gguf",        # gguf (default, standalone without Ollama) | auto | ollama | openai | off
    "tier": "auto",           # auto | nano | small | standard | off
    "preferred_model": "",    # specific GGUF filename inside models_dir (or Ollama tag)
    "models_dir": "models",   # folder where .gguf models are downloaded and loaded from
}

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

_GGUF_CACHE: dict[str, Any] = {}


def _meta_path() -> Path:
    index_dir = Path(os.environ.get("RAG_INDEX_DIR", REPO_ROOT / "rag" / "index"))
    return index_dir / "meta.json"


def _ensure_default_meta() -> None:
    """Ensures rag/index/meta.json exists in the repo folder even on a fresh git clone."""
    meta_path = _meta_path()
    if not meta_path.is_file():
        try:
            meta_path.parent.mkdir(parents=True, exist_ok=True)
            meta_path.write_text(
                json.dumps(
                    {
                        "documents_indexed": len(DEFAULT_CORPUS),
                        "source_ids": [d["id"] for d in DEFAULT_CORPUS],
                        "llm_config": dict(DEFAULT_LLM_CONFIG),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        except Exception:
            pass


_ensure_default_meta()


# ---------------------------------------------------------------------------
# Hardware Capability Detection & Configuration Management
# ---------------------------------------------------------------------------

def _get_memory_gb() -> tuple[float, float]:
    """Returns (total_ram_gb, available_ram_gb) using Python stdlib across Windows/Linux/macOS."""
    # Optional psutil if present
    try:
        import psutil  # type: ignore
        vm = psutil.virtual_memory()
        return round(vm.total / (1024 ** 3), 2), round(vm.available / (1024 ** 3), 2)
    except Exception:
        pass

    sys_name = platform.system().lower()
    if sys_name == "windows":
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):  # type: ignore[attr-defined]
                total = round(stat.ullTotalPhys / (1024 ** 3), 2)
                avail = round(stat.ullAvailPhys / (1024 ** 3), 2)
                return total, avail
        except Exception:
            pass
    elif sys_name == "linux":
        try:
            meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
            total_kb = avail_kb = 0
            for line in meminfo.splitlines():
                if line.startswith("MemTotal:"):
                    total_kb = int(line.split()[1])
                elif line.startswith("MemAvailable:"):
                    avail_kb = int(line.split()[1])
            if total_kb > 0:
                return round(total_kb / (1024 ** 2), 2), round(avail_kb / (1024 ** 2), 2)
        except Exception:
            pass
    elif sys_name == "darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, timeout=2.0).strip()
            total_b = int(out)
            total_gb = round(total_b / (1024 ** 3), 2)
            return total_gb, round(total_gb * 0.5, 2)
        except Exception:
            pass

    return 8.0, 4.0


def _get_gpu_info() -> tuple[str | None, float]:
    """Detects NVIDIA/dedicated GPU name and total VRAM in GB if available."""
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                text=True,
                timeout=2.0,
                stderr=subprocess.DEVNULL,
            ).strip()
            if out:
                first_line = out.splitlines()[0]
                parts = [p.strip() for p in first_line.split(",")]
                if len(parts) >= 2:
                    return parts[0], round(float(parts[1]) / 1024.0, 2)
        except Exception:
            pass
    return None, 0.0


def _list_ollama_models() -> tuple[bool, list[str]]:
    """Returns (server_reachable, list_of_installed_model_names)."""
    base_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=1.0) as resp:
            if resp.status == 200:
                tags_data = json.loads(resp.read().decode("utf-8"))
                models = [str(m.get("name")) for m in tags_data.get("models", []) if m.get("name")]
                return True, models
    except Exception:
        pass
    return False, []


def get_models_dir(custom_dir: str | Path | None = None) -> Path:
    """Resolves the directory where .gguf models are downloaded and loaded from.

    Priority:
      1. Explicit custom_dir argument (e.g. --models-dir)
      2. RAG_MODELS_DIR environment variable
      3. llm_config['models_dir'] inside rag/index/meta.json
      4. Default: <repo_root>/models
    """
    raw = str(custom_dir).strip() if custom_dir else ""
    if not raw:
        raw = os.environ.get("RAG_MODELS_DIR", "").strip()
    if not raw:
        meta_path = _meta_path()
        if meta_path.is_file():
            try:
                data = json.loads(meta_path.read_text(encoding="utf-8"))
                saved_dir = (data.get("llm_config") or {}).get("models_dir")
                if saved_dir:
                    raw = str(saved_dir).strip()
            except Exception:
                pass
    if not raw:
        return MODELS_DIR
    p = Path(raw).expanduser()
    if not p.is_absolute():
        p = REPO_ROOT / p
    return p.resolve()


def _list_gguf_models(models_dir: Path | None = None) -> list[dict[str, Any]]:
    """Lists .gguf model files present in the configured models directory."""
    target_dir = models_dir or get_models_dir()
    if not target_dir.is_dir():
        return []
    found: list[dict[str, Any]] = []
    for p in sorted(target_dir.glob("*.gguf")):
        if p.is_file():
            found.append({
                "name": p.name,
                "path": str(p),
                "size_mb": round(p.stat().st_size / (1024 ** 2), 1),
            })
    return found


def detect_hardware(models_dir: Path | None = None) -> dict[str, Any]:
    """Inspects PC hardware (RAM, CPU, disk, GPU) and available local LLM runtimes."""
    active_models_dir = models_dir or get_models_dir()
    total_ram_gb, avail_ram_gb = _get_memory_gb()
    gpu_name, vram_gb = _get_gpu_info()
    cpu_cores = os.cpu_count() or 2
    try:
        probe_path = active_models_dir if active_models_dir.exists() else active_models_dir.anchor or REPO_ROOT
        disk_free_gb = round(shutil.disk_usage(probe_path).free / (1024 ** 3), 2)
    except Exception:
        try:
            disk_free_gb = round(shutil.disk_usage(REPO_ROOT).free / (1024 ** 3), 2)
        except Exception:
            disk_free_gb = 0.0

    ollama_cli = shutil.which("ollama") is not None
    ollama_running, ollama_models = _list_ollama_models()
    gguf_models = _list_gguf_models(active_models_dir)
    llama_cpp_installed = importlib.util.find_spec("llama_cpp") is not None

    # Determine recommended model tier based on available RAM and GPU VRAM
    if avail_ram_gb < 2.0 and vram_gb < 4.0:
        recommended_tier = "off"
        reason = (
            f"Low available RAM ({avail_ram_gb} GB < 2.0 GB minimum). "
            "Retrieval-only mode recommended to prevent system freeze or timeout."
        )
    elif avail_ram_gb >= 8.0 or vram_gb >= 4.0:
        recommended_tier = "standard"
        reason = (
            f"High capacity detected ({avail_ram_gb} GB free RAM"
            + (f", GPU {gpu_name} {vram_gb} GB VRAM" if gpu_name else "")
            + "). Supports 'standard' (~3B), 'small' (~1.5B), and 'nano' (~0.5B) models."
        )
    elif avail_ram_gb >= 4.5:
        recommended_tier = "small"
        reason = (
            f"Medium capacity detected ({avail_ram_gb} GB free RAM, {cpu_cores} CPU threads). "
            "Supports 'small' (~1.5B) and 'nano' (~0.5B) models smoothly."
        )
    else:
        recommended_tier = "nano"
        reason = (
            f"Modest available RAM ({avail_ram_gb} GB free). "
            "Supports 'nano' (~0.5B, ~400 MB) lightweight models."
        )

    return {
        "os": f"{platform.system()} {platform.release()}",
        "architecture": platform.machine(),
        "cpu_cores": cpu_cores,
        "ram_total_gb": total_ram_gb,
        "ram_available_gb": avail_ram_gb,
        "disk_free_gb": disk_free_gb,
        "gpu_name": gpu_name,
        "vram_gb": vram_gb,
        "models_dir": str(active_models_dir),
        "ollama_installed": ollama_cli,
        "ollama_running": ollama_running,
        "ollama_models": ollama_models,
        "gguf_models": [m["name"] for m in gguf_models],
        "llama_cpp_installed": llama_cpp_installed,
        "recommended_tier": recommended_tier,
        "recommendation_reason": reason,
    }


def load_llm_config() -> dict[str, str]:
    """Loads active LLM configuration from rag/index/meta.json overlaid with environment variables."""
    cfg = dict(DEFAULT_LLM_CONFIG)
    meta_path = _meta_path()
    if meta_path.is_file():
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            saved = data.get("llm_config")
            if isinstance(saved, dict):
                for k in DEFAULT_LLM_CONFIG:
                    if saved.get(k) is not None:
                        cfg[k] = str(saved[k]).strip()
        except Exception:
            pass

    if os.environ.get("RAG_LLM_BACKEND"):
        cfg["backend"] = os.environ["RAG_LLM_BACKEND"].strip().lower()
    if os.environ.get("RAG_MODEL_TIER"):
        cfg["tier"] = os.environ["RAG_MODEL_TIER"].strip().lower()
    if os.environ.get("OLLAMA_MODEL"):
        cfg["preferred_model"] = os.environ["OLLAMA_MODEL"].strip()
    elif os.environ.get("RAG_GGUF_MODEL"):
        cfg["preferred_model"] = os.environ["RAG_GGUF_MODEL"].strip()
    if os.environ.get("RAG_MODELS_DIR"):
        cfg["models_dir"] = os.environ["RAG_MODELS_DIR"].strip()

    return cfg


def save_llm_config(
    backend: str | None = None,
    tier: str | None = None,
    preferred_model: str | None = None,
    models_dir: str | None = None,
) -> dict[str, Any]:
    """Saves LLM selection, models directory, and current hardware profile into rag/index/meta.json."""
    meta_path = _meta_path()
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "documents_indexed": len(DEFAULT_CORPUS),
        "source_ids": [d["id"] for d in DEFAULT_CORPUS],
    }
    if meta_path.is_file():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                payload.update(existing)
        except Exception:
            pass

    cfg = dict(DEFAULT_LLM_CONFIG)
    if isinstance(payload.get("llm_config"), dict):
        cfg.update(payload["llm_config"])

    if backend is not None:
        cfg["backend"] = backend.strip().lower()
    if tier is not None:
        cfg["tier"] = tier.strip().lower()
    if preferred_model is not None:
        cfg["preferred_model"] = preferred_model.strip()
    if models_dir is not None and models_dir.strip():
        cfg["models_dir"] = models_dir.strip()

    resolved_dir = get_models_dir(cfg.get("models_dir"))
    hw = detect_hardware(resolved_dir)
    payload["documents_indexed"] = int(payload.get("documents_indexed") or len(DEFAULT_CORPUS))
    payload["llm_config"] = cfg
    payload["hardware_detected"] = {
        "os": hw["os"],
        "cpu_cores": hw["cpu_cores"],
        "ram_total_gb": hw["ram_total_gb"],
        "ram_available_gb": hw["ram_available_gb"],
        "gpu_name": hw["gpu_name"],
        "vram_gb": hw["vram_gb"],
        "recommended_tier": hw["recommended_tier"],
    }

    meta_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _register_gguf_with_ollama(gguf_path: Path, model_tag: str) -> bool:
    """If Ollama CLI is installed and running, registers the local GGUF file so Ollama can serve it."""
    if not shutil.which("ollama"):
        return False
    modelfile_path = gguf_path.parent / f"{gguf_path.stem}.Modelfile"
    try:
        modelfile_content = (
            f'FROM "{gguf_path.resolve()}"\n'
            'TEMPLATE """<|im_start|>user\n{{ .Prompt }}<|im_end|>\n<|im_start|>assistant\n"""\n'
            "PARAMETER temperature 0.1\n"
            "PARAMETER num_predict 350\n"
            'PARAMETER stop "<|im_start|>"\n'
            'PARAMETER stop "<|im_end|>"\n'
            'PARAMETER stop "<|endoftext|>"\n'
        )
        modelfile_path.write_text(modelfile_content, encoding="utf-8")
        res = subprocess.run(
            ["ollama", "create", model_tag, "-f", str(modelfile_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return res.returncode == 0
    except Exception:
        return False
    finally:
        try:
            if modelfile_path.is_file():
                modelfile_path.unlink()
        except Exception:
            pass


def download_model(
    target: str = "auto",
    backend: str = "gguf",
    models_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Downloads a model suitable for the PC into the configured models folder (.gguf by default) or via Ollama."""
    target_dir = get_models_dir(models_dir)
    hw = detect_hardware(target_dir)
    resolved_tier = target.strip().lower()
    if resolved_tier == "auto":
        resolved_tier = hw["recommended_tier"]
        if resolved_tier == "off":
            resolved_tier = "nano"
        print(f"[Auto-Detect] Selected '{resolved_tier}' tier based on PC hardware ({hw['ram_available_gb']} GB free RAM).")

    chosen_backend = backend.strip().lower()
    if chosen_backend == "auto":
        # Default to standalone .gguf download (no Ollama dependency)
        chosen_backend = "gguf"

    # Case 1: Download via Ollama CLI
    if chosen_backend == "ollama":
        if not hw["ollama_installed"]:
            raise RuntimeError(
                "Ollama CLI is not installed on this PC. Use '--backend gguf' to download "
                f"a standalone .gguf file directly into '{target_dir}'."
            )
        model_tag = MODEL_CATALOG[resolved_tier]["ollama_model"] if resolved_tier in MODEL_CATALOG else target
        print(f"[Ollama] Pulling model '{model_tag}'...")
        proc = subprocess.run(["ollama", "pull", model_tag])
        if proc.returncode != 0:
            raise RuntimeError(f"'ollama pull {model_tag}' failed with exit code {proc.returncode}.")
        save_llm_config(
            backend="ollama",
            tier=resolved_tier if resolved_tier in MODEL_CATALOG else "auto",
            preferred_model=model_tag,
            models_dir=str(models_dir) if models_dir else None,
        )
        return {
            "status": "ok",
            "backend": "ollama",
            "model": model_tag,
            "tier": resolved_tier,
            "models_dir": str(target_dir),
        }

    # Case 2: Direct GGUF download into target_dir (configurable folder)
    if resolved_tier in MODEL_CATALOG:
        spec = MODEL_CATALOG[resolved_tier]
        url = spec["gguf_url"]
        filename = spec["gguf_filename"]
        expected_mb = float(spec["gguf_size_mb"])
    elif target.startswith("http://") or target.startswith("https://"):
        url = target
        filename = target.rstrip("/").split("/")[-1]
        if not filename.endswith(".gguf"):
            filename += ".gguf"
        expected_mb = 500.0
    else:
        raise ValueError(
            f"Unknown model tier '{target}'. Choose from: auto, nano, small, standard, or a direct https://...gguf URL."
        )

    required_gb = round((expected_mb * 1.2) / 1024.0, 2)
    if hw["disk_free_gb"] > 0 and hw["disk_free_gb"] < required_gb:
        raise RuntimeError(
            f"Insufficient disk space in '{target_dir}': {hw['disk_free_gb']} GB free, need at least {required_gb} GB."
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    dest_path = target_dir / filename
    part_path = target_dir / f"{filename}.part"

    if dest_path.is_file() and dest_path.stat().st_size > 1024 * 1024:
        print(f"[GGUF] File already exists at {dest_path} ({round(dest_path.stat().st_size / (1024**2), 1)} MB).")
    else:
        print(f"[GGUF] Downloading {filename} (~{int(expected_mb)} MB) from Hugging Face...")
        print(f"       URL:  {url}")
        print(f"       Dest: {dest_path}")
        req = urllib.request.Request(url, headers={"User-Agent": "AstroHealthCompanion/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(part_path, "wb") as out_file:
            total_bytes = int(resp.headers.get("Content-Length") or 0)
            downloaded = 0
            chunk_size = 1024 * 512
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_bytes > 0:
                    pct = min(100.0, downloaded * 100.0 / total_bytes)
                    filled = int(pct // 4)
                    bar = "#" * filled + "-" * (25 - filled)
                    mb_done = downloaded / (1024 ** 2)
                    mb_total = total_bytes / (1024 ** 2)
                    sys.stdout.write(f"\r       [{bar}] {pct:5.1f}% ({mb_done:6.1f} / {mb_total:6.1f} MB)")
                    sys.stdout.flush()
        print("\n[GGUF] Download complete.")
        part_path.replace(dest_path)

    active_backend = "gguf"
    active_model = dest_path.name
    save_llm_config(
        backend=active_backend,
        tier=resolved_tier if resolved_tier in MODEL_CATALOG else "auto",
        preferred_model=active_model,
        models_dir=str(models_dir) if models_dir else None,
    )
    return {
        "status": "ok",
        "backend": active_backend,
        "model": active_model,
        "models_dir": str(target_dir),
        "gguf_path": str(dest_path),
        "tier": resolved_tier,
    }


# ---------------------------------------------------------------------------
# Retrieval Pipeline
# ---------------------------------------------------------------------------

def _load_corpus() -> list[dict[str, Any]]:
    """Loads custom corpus from RAG_INDEX_DIR/corpus.json if present, else DEFAULT_CORPUS."""
    index_dir = Path(os.environ.get("RAG_INDEX_DIR", REPO_ROOT / "rag" / "index"))
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


# ---------------------------------------------------------------------------
# Multi-Backend LLM Generation (Ollama, Standalone GGUF, OpenAI-Compatible)
# ---------------------------------------------------------------------------

def _build_llm_prompt(question: str, alert: dict | None, citations: list[dict[str, str]]) -> str:
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

    return (
        "You are an offline astronaut health decision-support assistant. "
        "Keep your answer concise (3 to 5 sentences maximum) and follow these strict rules:\n"
        "1. Use ONLY the provided scientific sources and alert details.\n"
        "2. Cite sources inline as [1], [2].\n"
        "3. State the exact Rule ID (if an alert is given), plain-language explanation, and the exact suggested next step.\n"
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


def _select_best_ollama_model(models: list[str], preferred: str, target_tier: str) -> str | None:
    if not models:
        return None
    if preferred:
        for m in models:
            if m == preferred or m == f"{preferred}:latest" or m.split(":")[0] == preferred:
                return m

    tier_order = {
        "nano": ["0.5b", "1b", "nano"],
        "small": ["1.5b", "1b", "2b", "small", "0.5b"],
        "standard": ["3b", "4b", "7b", "8b", "standard", "1.5b", "1b"],
    }.get(target_tier, ["1.5b", "1b", "3b", "0.5b"])

    for token in tier_order:
        for m in models:
            if token in m.lower():
                return m
    return models[0]


def _try_ollama_generate(
    prompt: str,
    preferred_model: str = "",
    target_tier: str = "small",
) -> str | None:
    """Calls local Ollama server if reachable and a model is available; returns None on any error."""
    base_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    reachable, models = _list_ollama_models()
    if not reachable or not models:
        return None

    model = _select_best_ollama_model(models, preferred_model, target_tier)
    if not model:
        return None

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 350,
            "stop": ["<|im_end|>", "<|im_start|>", "<|endoftext|>", "\nQuestion:", "\nSources:"],
        },
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
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            return text if text else None
    except Exception:
        return None


def _select_best_gguf_file(preferred: str, target_tier: str, avail_ram_gb: float) -> Path | None:
    gguf_files = _list_gguf_models()
    if not gguf_files:
        return None

    # Filter out GGUF files whose size exceeds safe available RAM
    max_file_mb = max(450.0, (avail_ram_gb - 1.0) * 1024.0)
    compatible = [g for g in gguf_files if g["size_mb"] <= max_file_mb] or gguf_files

    if preferred:
        for g in compatible:
            if g["name"].lower() == preferred.lower() or preferred.lower() in g["name"].lower():
                return Path(g["path"])

    if target_tier in MODEL_CATALOG:
        expected_name = MODEL_CATALOG[target_tier]["gguf_filename"].lower()
        for g in compatible:
            if g["name"].lower() == expected_name:
                return Path(g["path"])

    # Pick lightest for nano, medium for small, largest compatible for standard
    if target_tier == "nano":
        compatible.sort(key=lambda x: x["size_mb"])
    elif target_tier == "standard":
        compatible.sort(key=lambda x: x["size_mb"], reverse=True)
    else:
        compatible.sort(key=lambda x: abs(x["size_mb"] - 1100.0))

    return Path(compatible[0]["path"])


def _try_gguf_generate(
    prompt: str,
    preferred_model: str = "",
    target_tier: str = "small",
    avail_ram_gb: float = 4.0,
) -> str | None:
    """Runs inference directly against a local .gguf file in ./models/ using llama-cpp-python if installed."""
    gguf_path = _select_best_gguf_file(preferred_model, target_tier, avail_ram_gb)
    if gguf_path is None or not gguf_path.is_file():
        return None

    try:
        from llama_cpp import Llama  # type: ignore
    except Exception:
        return None

    try:
        key = str(gguf_path.resolve())
        if key not in _GGUF_CACHE:
            threads = max(1, min(12, (os.cpu_count() or 4)))
            _GGUF_CACHE[key] = Llama(
                model_path=key,
                n_ctx=1024,
                n_batch=512,
                n_threads=threads,
                n_threads_batch=threads,
                n_gpu_layers=-1,
                verbose=False,
            )
        llm = _GGUF_CACHE[key]
        output = llm.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=110,
            temperature=0.1,
            stop=[
                "\n\nThis is a monitoring alert",
                "<|im_end|>",
                "<|endoftext|>",
                "\nQuestion:",
                "\nSources:",
            ],
        )
        choices = output.get("choices", []) if isinstance(output, dict) else []
        if choices:
            msg = choices[0].get("message") or {}
            text = (msg.get("content") or choices[0].get("text") or "").strip()
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
            if text and "not a diagnosis" not in text.lower():
                text = f"{text.rstrip('. ')}. This is a monitoring alert, not a diagnosis."
            return text if text else None
    except Exception:
        return None
    return None


def _try_openai_compat_generate(prompt: str, preferred_model: str = "") -> str | None:
    """Calls a local OpenAI-compatible server (e.g., LM Studio or llama-server) if configured."""
    base_url = os.environ.get("LOCAL_OPENAI_URL", "http://127.0.0.1:1234/v1").rstrip("/")
    payload = json.dumps({
        "model": preferred_model or "local-model",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 280,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
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
            choices = body.get("choices") or []
            if choices:
                text = ((choices[0].get("message") or {}).get("content") or "").strip()
                return text if text else None
    except Exception:
        return None
    return None


def _enforce_clinical_guardrails(text: str, alert: dict | None) -> str:
    """Ensures LLM responses never omit mandatory clinical safety disclaimers or rule identifiers."""
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    if alert is not None:
        rule_id = (alert.get("rule_id") or "").strip()
        if rule_id and rule_id.lower() not in cleaned.lower():
            cleaned = f"Rule {rule_id}: {cleaned}"
        boundary = CLINICAL_BOUNDARIES.get(rule_id, "")
        if boundary and "infer no health event" in boundary.lower() and "infer no health event" not in cleaned.lower():
            cleaned = f"{cleaned.rstrip('. ')}. {boundary}"
        next_step = (alert.get("next_step") or "").strip()
        if next_step and next_step[:20].lower() not in cleaned.lower():
            cleaned = f"{cleaned.rstrip('. ')}. Suggested next step: {next_step}."
        if "not a diagnosis" not in cleaned.lower():
            cleaned = f"{cleaned.rstrip('. ')}. This is a monitoring alert, not a diagnosis."
    return cleaned


def _generate_with_selected_llm(question: str, alert: dict | None, citations: list[dict[str, str]]) -> str | None:
    """Evaluates PC capabilities and active LLM config, then routes to the chosen local model backend."""
    # Respect test fixtures that explicitly disable local LLM by pointing OLLAMA_URL to port 1
    if os.environ.get("OLLAMA_URL", "").rstrip("/") in ("http://127.0.0.1:1", "http://localhost:1"):
        return None

    cfg = load_llm_config()
    backend = cfg.get("backend", "auto").lower()
    configured_tier = cfg.get("tier", "auto").lower()
    preferred_model = cfg.get("preferred_model", "")

    if backend in ("off", "retrieval_only", "none") or configured_tier in ("off", "retrieval_only", "none"):
        return None

    hw = detect_hardware()
    # Hardware guardrail: if PC has critically low free RAM (< 2.0 GB) and no GPU VRAM, skip LLM in auto mode
    if configured_tier == "auto" and hw["recommended_tier"] == "off":
        return None

    target_tier = hw["recommended_tier"] if configured_tier == "auto" else configured_tier
    prompt = _build_llm_prompt(question, alert, citations)

    raw_ans: str | None = None
    if backend == "ollama":
        raw_ans = _try_ollama_generate(prompt, preferred_model, target_tier)
    elif backend == "gguf":
        raw_ans = _try_gguf_generate(prompt, preferred_model, target_tier, hw["ram_available_gb"])
    elif backend in ("openai", "openai_compat", "lmstudio"):
        raw_ans = _try_openai_compat_generate(prompt, preferred_model)
    else:
        # backend == "auto": try standalone local GGUF first (no Ollama needed), then Ollama, then OpenAI-compatible
        raw_ans = _try_gguf_generate(prompt, preferred_model, target_tier, hw["ram_available_gb"])
        if not raw_ans:
            raw_ans = _try_ollama_generate(prompt, preferred_model, target_tier)
        if not raw_ans and os.environ.get("LOCAL_OPENAI_URL"):
            raw_ans = _try_openai_compat_generate(prompt, preferred_model)

    return _enforce_clinical_guardrails(raw_ans, alert) if raw_ans else None


# ---------------------------------------------------------------------------
# Public Contract Functions (used by backend/app/services/rag_adapter.py)
# ---------------------------------------------------------------------------

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
    """Answers a question grounded in S1-S9, using the configured local LLM when available or retrieval_only otherwise."""
    citations = _retrieve(question, alert)
    if not citations:
        return {
            "answer": NOT_FOUND,
            "mode": "retrieval_only",
            "citations": [],
        }

    llm_answer = _generate_with_selected_llm(question, alert, citations)
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


# ---------------------------------------------------------------------------
# CLI: Hardware Check, Model Selection & Interactive Downloader
# ---------------------------------------------------------------------------

def _print_status_report() -> dict[str, Any]:
    hw = detect_hardware()
    cfg = load_llm_config()
    print("=" * 72)
    print(" ASTRO-HEALTH COMPANION - PC HARDWARE & LOCAL LLM CAPABILITY REPORT")
    print("=" * 72)
    print(f" OS / Arch          : {hw['os']} ({hw['architecture']})")
    print(f" CPU Logical Cores  : {hw['cpu_cores']}")
    print(f" System RAM         : {hw['ram_available_gb']} GB available / {hw['ram_total_gb']} GB total")
    print(f" Free Disk Space    : {hw['disk_free_gb']} GB (at {hw['models_dir']})")
    print(f" Dedicated GPU      : {hw['gpu_name'] or 'None detected'} ({hw['vram_gb']} GB VRAM)")
    print("-" * 72)
    print(f" Recommended Tier   : {hw['recommended_tier'].upper()}")
    print(f" Assessment         : {hw['recommendation_reason']}")
    print("-" * 72)
    print(f" Models Directory   : {hw['models_dir']}")
    print(f" Ollama CLI / API   : installed={hw['ollama_installed']} | running={hw['ollama_running']}")
    print(f" Ollama Models      : {hw['ollama_models'] or 'None'}")
    print(f" Local GGUF Models  : {hw['gguf_models'] or 'None'}")
    print(f" llama-cpp-python   : installed={hw['llama_cpp_installed']}")
    print("-" * 72)
    print(" Active Configuration (rag/index/meta.json + env):")
    print(f"   backend          : {cfg['backend']}")
    print(f"   tier             : {cfg['tier']}")
    print(f"   preferred_model  : {cfg['preferred_model'] or '(auto)'}")
    print(f"   models_dir       : {cfg['models_dir']}")
    print("=" * 72)
    return hw


def _interactive_configure() -> None:
    hw = _print_status_report()
    cfg = load_llm_config()
    rec_tier = hw["recommended_tier"] if hw["recommended_tier"] != "off" else "nano"
    rec_spec = MODEL_CATALOG[rec_tier]

    print("\nSelect an action:")
    print(
        f"  [1] Download recommended model for this PC ({rec_spec['label']} - "
        f"~{rec_spec['gguf_size_mb']} MB)"
    )
    print("  [2] Choose a specific model tier to download (nano / small / standard)")
    print("  [3] Configure backend, tier, or models download folder without downloading")
    print("  [4] Disable LLM (use fast deterministic retrieval_only mode)")
    print("  [5] Exit without changes")

    choice = input("\nEnter option [1-5] (default 1): ").strip() or "1"
    if choice == "5":
        print("No changes made.")
        return

    if choice == "4":
        save_llm_config(backend="off", tier="off", preferred_model="")
        print("Saved configuration: LLM disabled (retrieval_only mode active).")
        return

    if choice in ("1", "2"):
        tier_to_get = rec_tier
        if choice == "2":
            print("\nAvailable model tiers:")
            for k, spec in MODEL_CATALOG.items():
                print(f"  - {k:8s}: {spec['label']} (~{spec['gguf_size_mb']} MB) -> {spec['description']}")
            picked = input(f"Choose tier [nano/small/standard] (default {rec_tier}): ").strip().lower()
            if picked in MODEL_CATALOG:
                tier_to_get = picked

        current_folder = cfg.get("models_dir", "models")
        custom_folder = input(
            f"Folder to store downloaded models (default '{current_folder}'): "
        ).strip() or current_folder

        default_dl_backend = "gguf"
        dl_backend = (
            input(f"Download method [gguf/ollama] (default {default_dl_backend}): ").strip().lower()
            or default_dl_backend
        )
        res = download_model(target=tier_to_get, backend=dl_backend, models_dir=custom_folder)
        print(f"\nConfiguration updated and saved to {_meta_path()}:")
        print(json.dumps(res, indent=2))
        if res["backend"] == "gguf" and not hw["llama_cpp_installed"]:
            print(
                "\nNote: To run standalone .gguf files without Ollama, install rag requirements:\n"
                "      pip install -r rag/requirements.txt"
            )
        return

    if choice == "3":
        backend = input("Backend [gguf/auto/ollama/openai/off] (default gguf): ").strip().lower() or "gguf"
        tier = input(f"Tier [auto/nano/small/standard/off] (default {hw['recommended_tier']}): ").strip().lower() or hw["recommended_tier"]
        pref = input("Preferred model name or GGUF filename (leave blank for auto): ").strip()
        current_folder = cfg.get("models_dir", "models")
        folder = input(f"Models folder path (default '{current_folder}'): ").strip() or current_folder
        save_llm_config(backend=backend, tier=tier, preferred_model=pref, models_dir=folder)
        print(f"Configuration saved to {_meta_path()}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Astro-Health Companion RAG & Local LLM Configuration Utility"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check PC hardware capabilities, installed models, and active RAG LLM settings.",
    )
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Run the interactive configuration and model download wizard.",
    )
    parser.add_argument(
        "--download",
        metavar="TIER_OR_URL",
        help="Download a model for this PC: auto, nano, small, standard, or a direct .gguf URL / Ollama tag.",
    )
    parser.add_argument(
        "--models-dir",
        metavar="FOLDER_PATH",
        default=None,
        help="Configure the folder where .gguf models are downloaded and loaded from (relative or absolute path).",
    )
    parser.add_argument(
        "--backend",
        choices=["auto", "ollama", "gguf", "openai", "off"],
        default=None,
        help="Set or use a specific LLM backend (auto, ollama, gguf, openai, off).",
    )
    parser.add_argument(
        "--set-tier",
        choices=["auto", "nano", "small", "standard", "off"],
        default=None,
        help="Set the active model capability tier in rag/index/meta.json.",
    )
    parser.add_argument(
        "--set-model",
        metavar="MODEL_NAME",
        default=None,
        help="Set a specific Ollama model tag or GGUF filename inside the models folder.",
    )
    parser.add_argument(
        "--question",
        metavar="TEXT",
        default=None,
        help="Run a test question through ask() and print the JSON result.",
    )

    args = parser.parse_args(argv)

    if args.configure:
        _interactive_configure()
        return 0

    if args.download:
        res = download_model(
            target=args.download,
            backend=args.backend or "gguf",
            models_dir=args.models_dir,
        )
        print(json.dumps(res, indent=2))
        return 0

    if args.backend or args.set_tier or args.set_model is not None or args.models_dir:
        updated = save_llm_config(
            backend=args.backend,
            tier=args.set_tier,
            preferred_model=args.set_model,
            models_dir=args.models_dir,
        )
        print("Updated rag/index/meta.json:")
        print(json.dumps(updated.get("llm_config"), indent=2))
        return 0

    if args.question:
        result = ask(args.question)
        print(json.dumps(result, indent=2))
        return 0

    # Default or --check: save current hardware snapshot and print report
    save_llm_config()
    _print_status_report()
    return 0


if __name__ == "__main__":
    sys.exit(main())
