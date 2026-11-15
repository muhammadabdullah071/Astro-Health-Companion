"""Central configuration. Every value can be overridden with an environment variable.

Values are read when called (not at import time) so tests and Docker can change them.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
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
    return os.environ.get("ASTRO_ID", "ASTRO-01")


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
    # Same resolution as rag.ask.index_dir(): relative paths are relative to the repo root.
    raw = os.environ.get("RAG_INDEX_DIR", "").strip()
    if not raw:
        return REPO_ROOT / "rag" / "index"
    p = Path(raw).expanduser()
    return p if p.is_absolute() else REPO_ROOT / p


def ask_timeout() -> float:
    return float(os.environ.get("ASK_TIMEOUT_SECONDS", "20"))


def stale_check_enabled() -> bool:
    """DATA-01 staleness (no new readings for a long time) is judged at request time against the clock.

    Off by default because the demo dataset is a fixed SIMULATED window: with the check on, the demo would
    start raising a stale-data notice 36 hours after its last reading. Switch it on (STALE_CHECK=true) for a
    live data feed, or pin the clock with ASTRO_NOW to rehearse the notice.
    """
    return os.environ.get("STALE_CHECK", "false").lower() in ("1", "true", "yes")


def reference_now() -> datetime:
    """The clock used for staleness and for default manual-entry times. ASTRO_NOW (UTC ISO) pins it for demos and tests."""
    raw = os.environ.get("ASTRO_NOW", "").strip()
    if raw:
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            logging.getLogger("astro.config").warning("Ignoring invalid ASTRO_NOW=%r", raw)
    return datetime.now(timezone.utc)
