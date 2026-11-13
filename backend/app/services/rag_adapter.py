"""Calls Cesar's RAG module safely.

Expected interface in rag/ask.py (agree this with Cesar):
    ask(question: str, alert: dict | None) -> {"answer": str, "mode": "llm" | "retrieval_only",
                                               "citations": [{"title","source","url","excerpt"}]}
    retrieval_only(question: str, alert: dict | None) -> same shape, no language model

If rag/ask.py is missing or fails to import, the placeholder stub is used instead.
The endpoint NEVER returns a 500 because of the model: on timeout or error it falls back
to retrieval-only mode.
"""
from __future__ import annotations

import importlib
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

from app import config
from app.services import rag_stub

logger = logging.getLogger("astro.rag")

_executor = ThreadPoolExecutor(max_workers=4)
_VALID_MODES = ("llm", "retrieval_only")


def _load_rag():
    root = str(config.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        return importlib.import_module("rag.ask")
    except Exception as exc:  # missing module or heavy dependency not installed
        logger.info("rag.ask not available (%s); using placeholder stub", exc)
        return None


def get_ask():
    mod = _load_rag()
    return getattr(mod, "ask", rag_stub.ask) if mod else rag_stub.ask


def get_retrieval_only():
    mod = _load_rag()
    return getattr(mod, "retrieval_only", rag_stub.retrieval_only) if mod else rag_stub.retrieval_only


def _normalise(raw: dict) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get("answer"), str):
        raise ValueError("RAG module returned an invalid response")
    citations = []
    for c in raw.get("citations") or []:
        if not isinstance(c, dict):
            continue
        citations.append({k: str(c.get(k, "")) for k in ("title", "source", "url", "excerpt")})
    mode = raw.get("mode") if raw.get("mode") in _VALID_MODES else "retrieval_only"
    return {"answer": raw["answer"], "mode": mode, "citations": citations, "disclaimer": config.DISCLAIMER}


def answer_question(question: str, alert: dict | None) -> dict:
    future = _executor.submit(get_ask(), question, alert)
    try:
        return _normalise(future.result(timeout=config.ask_timeout()))
    except Exception as exc:  # includes timeout
        future.cancel()
        logger.warning("ask() failed or timed out (%s: %s); using retrieval-only fallback", type(exc).__name__, exc)
    try:
        result = _normalise(get_retrieval_only()(question, alert))
        result["mode"] = "retrieval_only"
        return result
    except Exception:
        logger.exception("retrieval-only fallback failed")
        return {"answer": rag_stub.NOT_FOUND, "mode": "retrieval_only", "citations": [],
                "disclaimer": config.DISCLAIMER}
