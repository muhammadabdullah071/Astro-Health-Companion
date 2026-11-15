"""Download script for Ammara's 9 curated scientific sources (S1-S9).

Fetches official abstracts, open-access full texts (JATS XML / plain text from
Europe PMC, NCBI PMC BioC / E-utilities, OpenAlex, Crossref, and publisher OA pages),
and license metadata for S1-S9, saving them into `rag/sources/` (and optionally PDFs
when `--pdf` is passed).

Usage (from repo root):
    python -m rag.download_sources
    python -m rag.download_sources --pdf
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES_DIR = REPO_ROOT / "rag" / "sources"

USER_AGENT = (
    "AstroHealthCompanion-RAG/1.0 "
    "(https://github.com/muhammadabdullah071/Astro-Health-Companion; mailto:cesjavi@gmail.com)"
)

SOURCES_SPEC: list[dict[str, Any]] = [
    {
        "id": "S1",
        "title": "Human physiological limitations to long-term spaceflight and living in space",
        "authors": "Winkler LH",
        "journal": "Aerosp Med Hum Perform. 2023;94(6):444-456",
        "year": 2023,
        "doi": "10.3357/AMHP.6190.2023",
        "pmid": "37194175",
        "pmcid": None,
        "is_oa": False,
        "license": "subscription-abstract-only",
        "rules": [],
    },
    {
        "id": "S2",
        "title": "Long-term space missions' effects on the human organism: what we do know and what requires further research",
        "authors": "Tomsia M, Cieśla J, Śmieszek J, et al.",
        "journal": "Front Physiol. 2024;15:1284644",
        "year": 2024,
        "doi": "10.3389/fphys.2024.1284644",
        "pmid": None,
        "pmcid": "PMC10896920",
        "is_oa": True,
        "license": "cc-by-4.0",
        "rules": ["HR-01"],
    },
    {
        "id": "S3",
        "title": "The value of a spaceflight clinical decision support system for Earth-independent medical operations",
        "authors": "Russell BK, Burian BK, Hilmers DC, et al.",
        "journal": "npj Microgravity. 2023;9:46",
        "year": 2023,
        "doi": "10.1038/s41526-023-00284-1",
        "pmid": None,
        "pmcid": "PMC10284846",
        "is_oa": True,
        "license": "cc-by-4.0",
        "rules": ["HR-02", "DATA-02"],
    },
    {
        "id": "S4",
        "title": "Advancements in health monitoring technologies for astronauts in deep space missions: a review",
        "authors": "Gupta R, Ghosh PS",
        "journal": "Life Sci Space Res. 2025;47:190-196",
        "year": 2025,
        "doi": "10.1016/j.lssr.2025.06.011",
        "pmid": "41136019",
        "pmcid": None,
        "is_oa": False,
        "license": "subscription-abstract-only",
        "rules": ["HR-01", "SPO2-01", "TEMP-01", "DATA-01", "DATA-02"],
    },
    {
        "id": "S5",
        "title": "Enabling human space exploration missions through progressively Earth independent medical operations (EIMO)",
        "authors": "Levin DR, Steller J, Anderson A, et al.",
        "journal": "IEEE Open J Eng Med Biol. 2023;4:162-167",
        "year": 2023,
        "doi": "10.1109/OJEMB.2023.3255513",
        "pmid": None,
        "pmcid": "PMC10810302",
        "is_oa": True,
        "license": "cc-by-4.0",
        "rules": ["HR-02"],
    },
    {
        "id": "S6",
        "title": "Challenges for the human immune system after leaving Earth",
        "authors": "Marchal S, Choukér A, Bereiter-Hahn J, et al.",
        "journal": "npj Microgravity. 2024;10:106",
        "year": 2024,
        "doi": "10.1038/s41526-024-00446-9",
        "pmid": None,
        "pmcid": "PMC11574097",
        "is_oa": True,
        "license": "cc-by-4.0",
        "rules": ["TEMP-01"],
    },
    {
        "id": "S7",
        "title": "Biopsychosocial health considerations for astronauts in long-duration spaceflight: a narrative review",
        "authors": "Barbour BN, Twardowska K, Favero N, et al.",
        "journal": "Wilderness Environ Med. 2025;36(1_suppl):123S-137S",
        "year": 2025,
        "doi": "10.1177/10806032241289106",
        "pmid": "39470395",
        "pmcid": None,
        "is_oa": True,
        "license": "cc-by-nc",
        "rules": ["SLEEP-01", "SLEEP-02"],
    },
    {
        "id": "S8",
        "title": "Radiation risk mitigation in human space exploration: a primer, a vision, and the state of the art",
        "authors": "Narici L, Baiocco G, Cenci G, et al.",
        "journal": "Eur Phys J Plus. 2026;141:100",
        "year": 2026,
        "doi": "10.1140/epjp/s13360-025-07199-8",
        "pmid": None,
        "pmcid": None,
        "is_oa": True,
        "license": "cc-by-4.0",
        "rules": [],
    },
    {
        "id": "S9",
        "title": "Musculoskeletal responses to spaceflight: mechanisms, countermeasures, and key gaps",
        "authors": "Roberts BM, Deane CS, Szewczyk NJ, et al.",
        "journal": "Am J Physiol Cell Physiol. 2025;329(6):C1985-C1993",
        "year": 2025,
        "doi": "10.1152/ajpcell.00649.2025",
        "pmid": None,
        "pmcid": None,
        "is_oa": True,
        "license": "cc-by-4.0",
        "rules": [],
    },
]


def _http_get(url: str, timeout: int = 25) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception:
        return None


def _strip_xml_tags(xml_str: str) -> str:
    text = re.sub(r"<[^>]+>", " ", xml_str)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_pubmed_abstract(pmid: str) -> str | None:
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={pmid}&retmode=xml"
    )
    raw = _http_get(url)
    if not raw:
        return None
    try:
        root = ET.fromstring(raw)
        parts: list[str] = []
        for elem in root.findall(".//AbstractText"):
            label = elem.attrib.get("Label")
            chunk = "".join(elem.itertext()).strip()
            if chunk:
                parts.append(f"{label}: {chunk}" if label else chunk)
        if parts:
            return "\n\n".join(parts)
    except Exception:
        pass
    return None


def fetch_europepmc_metadata_and_abstract(
    doi: str | None,
    pmid: str | None,
    pmcid: str | None = None,
) -> dict[str, Any]:
    queries = []
    if doi:
        queries.append(urllib.parse.quote(f'DOI:"{doi}"'))
    if pmcid:
        queries.append(urllib.parse.quote(f"PMCID:{pmcid}"))
    if pmid:
        queries.append(urllib.parse.quote(f"EXT_ID:{pmid} AND SRC:MED"))

    for q in queries:
        url = (
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
            f"?query={q}&resultType=core&format=json"
        )
        raw = _http_get(url)
        if not raw:
            continue
        try:
            data = json.loads(raw.decode("utf-8"))
            results = data.get("resultList", {}).get("result", [])
            if results:
                r = results[0]
                return {
                    "abstract": _strip_xml_tags(r.get("abstractText", "")) if r.get("abstractText") else None,
                    "pmcid": r.get("pmcid"),
                    "pmid": r.get("pmid"),
                    "is_oa": r.get("isOpenAccess") == "Y",
                }
        except Exception:
            continue
    return {}


def fetch_crossref_abstract(doi: str) -> str | None:
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
    raw = _http_get(url)
    if not raw:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
        abstract_xml = data.get("message", {}).get("abstract")
        if abstract_xml:
            return _strip_xml_tags(abstract_xml)
    except Exception:
        pass
    return None


def fetch_openalex_abstract_and_oa(doi: str) -> dict[str, Any]:
    url = f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}"
    raw = _http_get(url)
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
        inv = data.get("abstract_inverted_index")
        abstract = None
        if isinstance(inv, dict) and inv:
            word_positions: list[tuple[int, str]] = []
            for word, positions in inv.items():
                for pos in positions:
                    word_positions.append((pos, word))
            word_positions.sort(key=lambda x: x[0])
            abstract = " ".join(w for _, w in word_positions).strip()
        oa = data.get("open_access") or {}
        best_oa = data.get("best_oa_location") or {}
        ids = data.get("ids") or {}
        pmid_url = ids.get("pmid") or ""
        pmcid_url = ids.get("pmcid") or ""
        resolved_pmid = pmid_url.rstrip("/").split("/")[-1] if pmid_url else None
        resolved_pmcid = pmcid_url.rstrip("/").split("/")[-1] if pmcid_url else None
        return {
            "abstract": abstract,
            "is_oa": bool(oa.get("is_oa")),
            "license": best_oa.get("license"),
            "pdf_url": best_oa.get("pdf_url") or oa.get("oa_url"),
            "pmid": resolved_pmid,
            "pmcid": resolved_pmcid,
        }
    except Exception:
        return {}


def fetch_pmc_fulltext(pmcid: str) -> str | None:
    # 1. Try Europe PMC fullTextXML
    url_epmc = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    raw = _http_get(url_epmc, timeout=35)
    if raw:
        try:
            root = ET.fromstring(raw)
            paragraphs: list[str] = []
            for sec in root.findall(".//body//sec"):
                title_el = sec.find("title")
                if title_el is not None:
                    sec_title = "".join(title_el.itertext()).strip()
                    if sec_title:
                        paragraphs.append(f"\n## {sec_title}\n")
                for p in sec.findall("p"):
                    p_text = " ".join("".join(p.itertext()).split())
                    if p_text:
                        paragraphs.append(p_text)
            if not paragraphs:
                body = root.find(".//body")
                if body is not None:
                    paragraphs.append(" ".join("".join(body.itertext()).split()))
            text = "\n\n".join(paragraphs).strip()
            if len(text) > 500:
                return text
        except Exception:
            pass

    # 2. Try NCBI BioC JSON API for PMC
    url_bioc = (
        "https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/"
        f"BioC_json/{pmcid}/unicode"
    )
    raw_bioc = _http_get(url_bioc, timeout=35)
    if raw_bioc:
        try:
            data = json.loads(raw_bioc.decode("utf-8"))
            docs = data if isinstance(data, list) else [data]
            passages: list[str] = []
            for d in docs:
                for doc_item in d.get("documents", []):
                    for passage in doc_item.get("passages", []):
                        txt = (passage.get("text") or "").strip()
                        if txt:
                            passages.append(txt)
            text = "\n\n".join(passages).strip()
            if len(text) > 500:
                return text
        except Exception:
            pass

    # 3. Try NCBI EFetch PMC XML
    pmc_num = pmcid.replace("PMC", "")
    url_efetch = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pmc&id={pmc_num}&retmode=xml"
    )
    raw_efetch = _http_get(url_efetch, timeout=35)
    if raw_efetch:
        try:
            root = ET.fromstring(raw_efetch)
            body = root.find(".//body")
            if body is not None:
                text = " ".join("".join(body.itertext()).split())
                if len(text) > 500:
                    return text
        except Exception:
            pass

    return None


def fetch_springer_or_publisher_fulltext(doi: str) -> str | None:
    """Fallback HTML/XML reader for open-access publisher articles (e.g. S8 Springer EPJ Plus)."""
    urls = [f"https://doi.org/{doi}"]
    if "10.1140/epjp/" in doi:
        urls.insert(0, f"https://link.springer.com/article/{doi}")
    for url in urls:
        raw = _http_get(url, timeout=30)
        if not raw:
            continue
        try:
            html_str = raw.decode("utf-8", errors="ignore")
            paras = re.findall(r"<p[^>]*>(.*?)</p>", html_str, flags=re.DOTALL | re.IGNORECASE)
            cleaned = []
            for p in paras:
                txt = _strip_xml_tags(p)
                if (
                    len(txt) > 90
                    and not txt.lower().startswith("cookies")
                    and "springer nature" not in txt.lower()
                ):
                    cleaned.append(txt)
            joined = "\n\n".join(cleaned).strip()
            if len(joined) > 1000:
                return joined
        except Exception:
            continue
    return None


def download_sources(
    sources_dir: Path | None = None,
    download_pdfs: bool = False,
) -> dict[str, Any]:
    target_dir = Path(sources_dir or DEFAULT_SOURCES_DIR)
    target_dir.mkdir(parents=True, exist_ok=True)

    metadata_out: dict[str, Any] = {}
    summary = {
        "sources_dir": str(target_dir),
        "abstracts_saved": 0,
        "fulltexts_saved": 0,
        "pdfs_saved": 0,
        "sources": {},
    }

    for spec in SOURCES_SPEC:
        sid = spec["id"]
        doi = spec["doi"]
        pmid = spec["pmid"]
        pmcid = spec["pmcid"]
        print(f"[{sid}] Fetching {spec['title'][:65]}...")

        # 1. Query Europe PMC by DOI / PMCID / verified PMID first
        epmc_info = fetch_europepmc_metadata_and_abstract(doi, pmid, pmcid)
        abstract: str | None = epmc_info.get("abstract")
        if not pmcid and epmc_info.get("pmcid"):
            pmcid = epmc_info["pmcid"]
        if not pmid and epmc_info.get("pmid"):
            pmid = epmc_info["pmid"]

        # 2. Query OpenAlex by DOI
        oa_info = fetch_openalex_abstract_and_oa(doi)
        if not abstract and oa_info.get("abstract"):
            abstract = oa_info["abstract"]
        if not pmid and oa_info.get("pmid"):
            pmid = oa_info["pmid"]
        if not pmcid and oa_info.get("pmcid"):
            pmcid = oa_info["pmcid"]

        # 3. Query PubMed by verified/resolved PMID
        if not abstract and pmid:
            abstract = fetch_pubmed_abstract(pmid)

        # 4. Query Crossref by DOI
        if not abstract:
            abstract = fetch_crossref_abstract(doi)

        # Save abstract file
        abstract_file = target_dir / f"{sid}_abstract.txt"
        if abstract:
            header = (
                f"Source ID: {sid}\n"
                f"Title: {spec['title']}\n"
                f"Authors: {spec['authors']}\n"
                f"Journal: {spec['journal']}\n"
                f"DOI: https://doi.org/{doi}\n"
                f"PMID: {pmid or 'N/A'} | PMCID: {pmcid or 'N/A'}\n"
                f"License: {spec['license']}\n"
                f"{'=' * 72}\n\n"
            )
            abstract_file.write_text(header + abstract.strip() + "\n", encoding="utf-8")
            summary["abstracts_saved"] += 1
            print(f"  -> Saved {abstract_file.name} ({len(abstract)} chars)")

        # Fetch open-access full text when available
        fulltext: str | None = None
        ft_filename: str | None = None
        if pmcid:
            fulltext = fetch_pmc_fulltext(pmcid)
            if fulltext:
                ft_filename = f"{sid}_{pmcid}.txt"
        if not fulltext and spec["is_oa"]:
            fulltext = fetch_springer_or_publisher_fulltext(doi)
            if fulltext:
                tag = pmcid or "PMC_OA"
                ft_filename = f"{sid}_{tag}.txt"

        if fulltext and ft_filename:
            ft_path = target_dir / ft_filename
            header = (
                f"Source ID: {sid} (Open-Access Full Text)\n"
                f"Title: {spec['title']}\n"
                f"Authors: {spec['authors']}\n"
                f"Journal: {spec['journal']}\n"
                f"DOI: https://doi.org/{doi}\n"
                f"PMID: {pmid or 'N/A'} | PMCID: {pmcid or 'N/A'}\n"
                f"License: {spec['license']}\n"
                f"{'=' * 72}\n\n"
            )
            ft_path.write_text(header + fulltext.strip() + "\n", encoding="utf-8")
            summary["fulltexts_saved"] += 1
            print(f"  -> Saved {ft_path.name} ({len(fulltext)} chars)")

        # Optional PDF download for Open Access articles
        pdf_saved = False
        if download_pdfs and spec["is_oa"]:
            pdf_urls = []
            if oa_info.get("pdf_url"):
                pdf_urls.append(oa_info["pdf_url"])
            if "10.1038/" in doi:
                article_slug = doi.split("10.1038/", 1)[1]
                pdf_urls.append(f"https://www.nature.com/articles/{article_slug}.pdf")
            if "10.1140/epjp" in doi:
                pdf_urls.append(f"https://link.springer.com/content/pdf/{doi}.pdf")
            if pmcid:
                pdf_urls.append(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextPdf")

            for purl in pdf_urls:
                raw_pdf = _http_get(purl, timeout=45)
                if raw_pdf and raw_pdf.startswith(b"%PDF"):
                    pdf_path = target_dir / f"{sid}.pdf"
                    pdf_path.write_bytes(raw_pdf)
                    summary["pdfs_saved"] += 1
                    pdf_saved = True
                    print(f"  -> Saved {pdf_path.name} ({len(raw_pdf) // 1024} KB)")
                    break

        metadata_out[sid] = {
            "id": sid,
            "title": spec["title"],
            "authors": spec["authors"],
            "journal": spec["journal"],
            "year": spec["year"],
            "doi": doi,
            "url": f"https://doi.org/{doi}",
            "pmid": pmid,
            "pmcid": pmcid,
            "is_oa": spec["is_oa"],
            "license": oa_info.get("license") or spec["license"],
            "rules": spec["rules"],
            "abstract": abstract or "",
            "abstract_file": abstract_file.name if abstract else None,
            "fulltext_file": ft_filename,
            "fulltext_chars": len(fulltext) if fulltext else 0,
            "pdf_downloaded": pdf_saved,
        }
        summary["sources"][sid] = {
            "abstract_chars": len(abstract) if abstract else 0,
            "fulltext_chars": len(fulltext) if fulltext else 0,
            "pdf_saved": pdf_saved,
        }
        time.sleep(0.35)

    meta_path = target_dir / "sources_metadata_and_licenses.json"
    meta_path.write_text(
        json.dumps(metadata_out, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"\nSaved metadata and license manifest to {meta_path}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download Ammara's 9 curated scientific sources (S1-S9) into rag/sources/."
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Target directory for downloaded sources (default: rag/sources)",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also download open-access PDF files when available (gitignored by default)",
    )
    args = parser.parse_args()
    out_dir = Path(args.dir) if args.dir else DEFAULT_SOURCES_DIR
    result = download_sources(sources_dir=out_dir, download_pdfs=args.pdf)
    print(
        f"Done: {result['abstracts_saved']}/9 abstracts, "
        f"{result['fulltexts_saved']} full-text papers saved in {result['sources_dir']}."
    )


if __name__ == "__main__":
    main()
