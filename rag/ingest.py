"""Ingestion pipeline for Ammara's 9 curated scientific sources (S1-S9).

Reads downloaded abstracts and open-access full texts from ../data/sources_s1_s9
(when present on the local machine) and merges them with the verified citation
metadata and clinical boundaries in rag/ask.py, writing:
  - rag/index/corpus.json
  - rag/index/meta.json ({"documents_indexed": 9})

Usage (from repo root):
    python -m rag.ingest
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from rag.ask import DEFAULT_CORPUS


def build_index(sources_dir: Path | None = None, index_dir: Path | None = None) -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    index_dir = Path(index_dir or os.environ.get("RAG_INDEX_DIR", repo_root / "rag" / "index"))
    sources_dir = Path(sources_dir or (repo_root.parent / "data" / "sources_s1_s9"))

    index_dir.mkdir(parents=True, exist_ok=True)
    corpus = copy.deepcopy(DEFAULT_CORPUS)

    meta_file = sources_dir / "sources_metadata_and_licenses.json"
    downloaded_meta = {}
    if meta_file.is_file():
        try:
            downloaded_meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            downloaded_meta = {}

    enriched_count = 0
    for doc in corpus:
        sid = doc["id"]
        info = downloaded_meta.get(sid, {})
        abstract_path = sources_dir / f"{sid}_abstract.txt"
        fulltext_matches = list(sources_dir.glob(f"{sid}_PMC*.txt")) if sources_dir.is_dir() else []

        if abstract_path.is_file():
            doc["abstract"] = abstract_path.read_text(encoding="utf-8").strip()
            enriched_count += 1
        elif info.get("abstract"):
            doc["abstract"] = info["abstract"]
            enriched_count += 1

        if fulltext_matches:
            ft_text = fulltext_matches[0].read_text(encoding="utf-8", errors="ignore").strip()
            doc["fulltext_chars"] = len(ft_text)
            doc["fulltext_preview"] = ft_text[:1500]
        else:
            doc["fulltext_chars"] = 0

        doc["is_open_access"] = info.get("is_oa", sid in ("S2", "S3", "S5", "S6", "S7", "S8", "S9"))
        doc["license"] = info.get("license") or ("cc-by-nc" if sid == "S7" else ("cc-by" if doc["is_open_access"] else "subscription-abstract-only"))

    (index_dir / "corpus.json").write_text(
        json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    meta_payload = {
        "documents_indexed": len(corpus),
        "sources_enriched_from_disk": enriched_count,
        "source_ids": [d["id"] for d in corpus],
    }
    (index_dir / "meta.json").write_text(
        json.dumps(meta_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return meta_payload


if __name__ == "__main__":
    result = build_index()
    print(f"Indexed {result['documents_indexed']} sources into rag/index/ (enriched={result['sources_enriched_from_disk']}): {result['source_ids']}")
