"""Stand-in for Cesar's RAG module, used until rag/ask.py exists.

Same signatures as the real module, so swapping is automatic (see rag_adapter.py).
Everything here is clearly marked PLACEHOLDER so it can never pass as a real source.
"""
from __future__ import annotations

PLACEHOLDER_CITATIONS = [
    {
        "title": "PLACEHOLDER source 1 (replace with a paper from Ammara's list)",
        "source": "NASA",
        "url": "https://example.org/placeholder-1",
        "excerpt": "Placeholder excerpt used only for UI and integration development.",
    },
    {
        "title": "PLACEHOLDER source 2 (replace with a paper from Ammara's list)",
        "source": "PubMed",
        "url": "https://example.org/placeholder-2",
        "excerpt": "Placeholder excerpt used only for UI and integration development.",
    },
]

NOT_FOUND = "I cannot answer that from my sources."


def retrieval_only(question, alert=None):
    if alert is None:
        return {"answer": NOT_FOUND, "mode": "retrieval_only", "citations": []}
    return {
        "answer": ("The language model is unavailable, so here are the most relevant excerpts from the local "
                   f"library. [PLACEHOLDER] {alert['message']}"),
        "mode": "retrieval_only",
        "citations": PLACEHOLDER_CITATIONS[:1],
    }


def ask(question, alert=None):
    if alert is None:
        return retrieval_only(question, None)
    step = alert.get("next_step") or "Re-measure and follow mission medical procedure."
    return {
        "answer": (f"[PLACEHOLDER ANSWER] {alert['message']} The rule that fired was "
                   f"'{alert['rule']}'. Possible contributing factors will come from the scientific library [1][2]. "
                   f"Suggested next step: {step}"),
        "mode": "llm",
        "citations": PLACEHOLDER_CITATIONS,
    }
