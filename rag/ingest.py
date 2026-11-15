"""Ingestion pipeline for Ammara's 9 curated scientific sources (S1-S9).

Reads downloaded abstracts and open-access full texts from `rag/sources`
(or `../data/sources_s1_s9` if present), splits full-text articles and abstracts
into searchable evidence chunks, and merges them with the verified citation
metadata and clinical boundaries in `rag/ask.py`, writing:
  - rag/index/corpus.json
  - rag/index/meta.json ({"documents_indexed": 9, ...})

Usage (from repo root):
    python -m rag.ingest
    python -m rag.ingest --download
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path

from rag.ask import DEFAULT_CORPUS, DEFAULT_LLM_CONFIG, detect_hardware, index_dir as default_index_dir


def _strip_header(text: str) -> str:
    sep = "=" * 72
    if sep in text:
        text = text.split(sep, 1)[1]
    return text.strip()


def _chunk_text(text: str, max_chars: int = 550, max_chunks: int = 25) -> list[str]:
    """Splits an abstract or full-text article into clean, substantive paragraph chunks."""
    if not text:
        return []
    raw_paras = re.split(r"\n\s*\n+", text.replace("\r\n", "\n"))
    chunks: list[str] = []
    current_heading = ""

    for para in raw_paras:
        cleaned = re.sub(r"\s+", " ", para).strip()
        if not cleaned:
            continue
        if cleaned.startswith("#"):
            current_heading = cleaned.lstrip("#").strip()
            continue
        low = cleaned.lower()
        if len(cleaned) < 80 or low.startswith(("references", "acknowledg", "competing interest", "publisher's note")):
            continue
        prefix = f"[{current_heading}] " if current_heading and not cleaned.startswith("[") else ""
        passage = f"{prefix}{cleaned}"
        if len(passage) > max_chars:
            sentences = re.split(r"(?<=[.!?])\s+", passage)
            buf = ""
            for sent in sentences:
                if len(buf) + len(sent) + 1 <= max_chars:
                    buf = f"{buf} {sent}".strip() if buf else sent
                else:
                    if len(buf) >= 80:
                        chunks.append(buf)
                    buf = f"{prefix}{sent}".strip() if prefix and not sent.startswith("[") else sent
                    if len(chunks) >= max_chunks:
                        break
            if buf and len(buf) >= 80 and len(chunks) < max_chunks:
                chunks.append(buf)
        else:
            chunks.append(passage)
        if len(chunks) >= max_chunks:
            break

    return chunks[:max_chunks]


def resolve_sources_dir(custom_dir: Path | None = None) -> Path:
    """Resolves the directory containing S1-S9 abstracts and open-access full texts."""
    if custom_dir is not None:
        return Path(custom_dir)
    repo_root = Path(__file__).resolve().parents[1]
    for candidate in (
        repo_root / "rag" / "sources",
        repo_root / "rag" / "sources_s1_s9",
        repo_root.parent / "data" / "sources_s1_s9",
    ):
        if candidate.is_dir():
            return candidate
    return repo_root / "rag" / "sources"


def build_index(
    sources_dir: Path | None = None,
    index_dir: Path | None = None,
    detect_hw: bool = True,
) -> dict:
    index_dir = Path(index_dir) if index_dir else default_index_dir()
    sources_dir = resolve_sources_dir(sources_dir)

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
    total_chunks = 0
    for doc in corpus:
        sid = doc["id"]
        info = downloaded_meta.get(sid, {})
        abstract_path = sources_dir / f"{sid}_abstract.txt"
        fulltext_matches = list(sources_dir.glob(f"{sid}_PMC*.txt")) if sources_dir.is_dir() else []

        abstract_text = ""
        if abstract_path.is_file():
            abstract_text = _strip_header(abstract_path.read_text(encoding="utf-8", errors="ignore"))
            doc["abstract"] = abstract_text
            enriched_count += 1
        elif info.get("abstract"):
            abstract_text = str(info["abstract"]).strip()
            doc["abstract"] = abstract_text
            enriched_count += 1

        doc_chunks: list[str] = []
        if abstract_text:
            doc_chunks.extend(_chunk_text(f"# Abstract\n\n{abstract_text}", max_chars=550, max_chunks=3))

        if fulltext_matches:
            ft_text = _strip_header(fulltext_matches[0].read_text(encoding="utf-8", errors="ignore"))
            doc["fulltext_chars"] = len(ft_text)
            doc["fulltext_preview"] = ft_text[:1500]
            ft_chunks = _chunk_text(ft_text, max_chars=550, max_chunks=22)
            for ch in ft_chunks:
                if ch not in doc_chunks:
                    doc_chunks.append(ch)
        else:
            doc["fulltext_chars"] = 0

        doc["chunks"] = doc_chunks
        total_chunks += len(doc_chunks)
        doc["is_open_access"] = info.get("is_oa", sid in ("S2", "S3", "S5", "S6", "S7", "S8", "S9"))
        doc["license"] = info.get("license") or (
            "cc-by-nc" if sid == "S7" else ("cc-by" if doc["is_open_access"] else "subscription-abstract-only")
        )

    (index_dir / "corpus.json").write_text(
        json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    existing_llm_config = dict(DEFAULT_LLM_CONFIG)
    meta_json_path = index_dir / "meta.json"
    if meta_json_path.is_file():
        try:
            old_meta = json.loads(meta_json_path.read_text(encoding="utf-8"))
            if isinstance(old_meta.get("llm_config"), dict):
                existing_llm_config.update(old_meta["llm_config"])
        except Exception:
            pass

    meta_payload = {
        "documents_indexed": len(corpus),
        "sources_enriched_from_disk": enriched_count,
        "chunks_indexed": total_chunks,
        "source_ids": [d["id"] for d in corpus],
        "llm_config": existing_llm_config,
    }
    if detect_hw:  # informational only; skipped when the index is auto-built at startup
        hw = detect_hardware()
        meta_payload["hardware_detected"] = {
            "os": hw["os"],
            "cpu_cores": hw["cpu_cores"],
            "ram_total_gb": hw["ram_total_gb"],
            "ram_available_gb": hw["ram_available_gb"],
            "gpu_name": hw["gpu_name"],
            "vram_gb": hw["vram_gb"],
            "recommended_tier": hw["recommended_tier"],
        }
    meta_json_path.write_text(
        json.dumps(meta_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    return meta_payload


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest S1-S9 scientific sources into rag/index/.")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download S1-S9 abstracts and open-access full texts into rag/sources/ before indexing",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also download open-access PDFs when --download is used",
    )
    args = parser.parse_args()
    if args.download:
        from rag.download_sources import download_sources

        download_sources(download_pdfs=args.pdf)
    result = build_index()
    print(
        f"Indexed {result['documents_indexed']} sources into rag/index/ "
        f"(enriched={result['sources_enriched_from_disk']}, chunks={result['chunks_indexed']}): "
        f"{result['source_ids']}"
    )
