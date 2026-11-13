"""Central configuration. Every value can be overridden with an environment variable.

Values are read when called (not at import time) so tests and Docker can change them.
"""
from __future__ import annotations

import os
from pathlib import Path

# backend/app/config.py -> parents[2] is the repository root
REPO_ROOT = Path(__file__).resolve().parents[2]

def load_env_file(path: Path) -> int:
    """Load KEY=VALUE lines from a .env file. No extra package needed.

    Priority: real environment variables win, then the .env file, then the defaults below.
    A missing file is fine (returns 0). Lines starting with # are comments.
    """
    path = Path(path)
    if not path.is_file():
        return 0
    loaded = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


# Optional .env at the repo root (or the file named by ENV_FILE). Safe to skip.
load_env_file(Path(os.environ.get("ENV_FILE", REPO_ROOT / ".env")))

DATA_LABEL = "SIMULATED"
DISCLAIMER = "Decision support only - not a medical diagnosis."


def default_astronaut_id() -> str:
    return os.environ.get("ASTRO_ID", "astro-demo-1")


def db_path() -> Path:
    return Path(os.environ.get("ASTRO_DB_PATH", REPO_ROOT / "data" / "runtime" / "astro.db"))


def sample_csv_path() -> Path:
    return Path(os.environ.get("ASTRO_SAMPLE_CSV", REPO_ROOT / "data" / "sample" / "readings.csv"))


def examples_dir() -> Path:
    return REPO_ROOT / "contract" / "examples"


def cors_origins() -> list[str]:
    raw = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,http://127.0.0.1:3000,http://127.0.0.1:3001",
    )
    return [o.strip() for o in raw.split(",") if o.strip()]


def ollama_url() -> str:
    return os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")


def offline_mode() -> bool:
    return os.environ.get("OFFLINE_MODE", "true").lower() in ("1", "true", "yes")


def rag_index_dir() -> Path:
    return Path(os.environ.get("RAG_INDEX_DIR", REPO_ROOT / "rag" / "index"))


def ask_timeout() -> float:
    return float(os.environ.get("ASK_TIMEOUT_SECONDS", "20"))
