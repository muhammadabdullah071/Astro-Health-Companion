"""Real checks used by /api/status. Nothing here is hardcoded."""
from __future__ import annotations

import json
import urllib.request

from app import config


def probe_llm(timeout: float = 1.0) -> bool:
    """True when the local Ollama server answers quickly."""
    url = config.ollama_url().rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def documents_indexed() -> int:
    """Reads rag/index/meta.json written by Cesar's ingest: {"documents_indexed": 12}."""
    try:
        data = json.loads((config.rag_index_dir() / "meta.json").read_text(encoding="utf-8"))
        return int(data.get("documents_indexed", 0))
    except Exception:
        return 0
