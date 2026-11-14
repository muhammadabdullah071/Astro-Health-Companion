# RAG & Scientific Knowledge Library (`rag/`)

**Owner:** Cesar

Provides offline-capable source ingestion, indexing, evidence retrieval, clinical boundary enforcement, and response generation (`llm` and `retrieval_only` modes) for `POST /api/assistant/ask` and `GET /api/status`.

---

## 1. Curated Scientific Library (Ammara's 9 Sources: `S1`–`S9`)

All 9 sources from Section 5 of Ammara's deliverables pack are indexed with stable DOI links and explicit clinical boundaries. None of these sources establishes a clinical numeric cut-off; all numeric triggers in the monitoring engine are prototype workflow rules compared against personal baselines.

| ID | Citation | Identifier / Link | Rule Mapping | Access & License Verification |
|---|---|---|---|---|
| **S1** | Winkler LH. *Human physiological limitations to long-term spaceflight and living in space.* Aerosp Med Hum Perform. 2023;94(6):444-456. | [doi:10.3357/AMHP.6190.2023](https://doi.org/10.3357/AMHP.6190.2023) (PMID 37194175) | General spaceflight context | Closed / Subscription (public abstract indexed) |
| **S2** | Tomsia M, Cieśla J, Śmieszek J, et al. *Long-term space missions' effects on the human organism: what we do know and what requires further research.* Front Physiol. 2024;15:1284644. | [doi:10.3389/fphys.2024.1284644](https://doi.org/10.3389/fphys.2024.1284644) (PMC10896920) | `HR-01` | **Gold Open Access (`CC-BY 4.0`)** — Full text & abstract verified |
| **S3** | Russell BK, Burian BK, Hilmers DC, et al. *The value of a spaceflight clinical decision support system for Earth-independent medical operations.* npj Microgravity. 2023;9:46. | [doi:10.1038/s41526-023-00284-1](https://doi.org/10.1038/s41526-023-00284-1) (PMC10284846) | `HR-02`, `DATA-02` | **Gold Open Access (`CC-BY 4.0`)** — Full text & abstract verified |
| **S4** | Gupta R, Ghosh PS. *Advancements in health monitoring technologies for astronauts in deep space missions: a review.* Life Sci Space Res. 2025;47:190-196. | [doi:10.1016/j.lssr.2025.06.011](https://doi.org/10.1016/j.lssr.2025.06.011) (PMID 41136019) | `HR-01`, `SPO2-01`, `TEMP-01`, `DATA-01`, `DATA-02` | **Closed / Subscription** — Confirmed abstract-level access only |
| **S5** | Levin DR, Steller J, Anderson A, et al. *Enabling human space exploration missions through progressively Earth independent medical operations (EIMO).* IEEE Open J Eng Med Biol. 2023;4:162-167. | [doi:10.1109/OJEMB.2023.3255513](https://doi.org/10.1109/OJEMB.2023.3255513) (PMC10810302) | `HR-02` | **Gold Open Access (`CC-BY 4.0`)** — Full text & abstract verified |
| **S6** | Marchal S, Choukér A, Bereiter-Hahn J, et al. *Challenges for the human immune system after leaving Earth.* npj Microgravity. 2024;10:106. | [doi:10.1038/s41526-024-00446-9](https://doi.org/10.1038/s41526-024-00446-9) (PMC11574097) | `TEMP-01` | **Gold Open Access (`CC-BY 4.0`)** — Full text & abstract verified |
| **S7** | Barbour BN, Twardowska K, Favero N, et al. *Biopsychosocial health considerations for astronauts in long-duration spaceflight: a narrative review.* Wilderness Environ Med. 2025;36(1_suppl):123S-137S. | [doi:10.1177/10806032241289106](https://doi.org/10.1177/10806032241289106) (PMID 39470395) | `SLEEP-01`, `SLEEP-02` | **Hybrid Open Access (`CC-BY-NC`)** — Non-commercial attribution license verified |
| **S8** | Narici L, Baiocco G, Cenci G, et al. *Radiation risk mitigation in human space exploration: a primer, a vision, and the state of the art.* Eur Phys J Plus. 2026;141:100. | [doi:10.1140/epjp/s13360-025-07199-8](https://doi.org/10.1140/epjp/s13360-025-07199-8) | Radiation context | **Hybrid Open Access (`CC-BY 4.0`)** — Full text & abstract verified |
| **S9** | Roberts BM, Deane CS, Szewczyk NJ, et al. *Musculoskeletal responses to spaceflight: mechanisms, countermeasures, and key gaps.* Am J Physiol Cell Physiol. 2025;329(6):C1985-C1993. | [doi:10.1152/ajpcell.00649.2025](https://doi.org/10.1152/ajpcell.00649.2025) | Musculoskeletal context | **Hybrid Open Access (`CC-BY 4.0`)** — Abstract verified |

---

## 2. Interface & Safety Boundaries (`rag/ask.py`)

`backend/app/services/rag_adapter.py` imports `rag.ask` automatically:

```python
ask(question: str, alert: dict | None = None) -> dict
retrieval_only(question: str, alert: dict | None = None) -> dict
```

- **Zero extra dependencies**: Uses Python's standard library only, so it runs inside `backend`'s existing environment and Docker container without internet access.
- **Automatic `rag/index/meta.json` creation**: Importing `rag.ask` ensures `rag/index/meta.json` (`{"documents_indexed": 9}`) exists even on a fresh git clone where `rag/index/*` is gitignored.
- **Clinical & Wording Guardrails**:
  - Follows Section 4 alert explanation structure (`SEVERITY`, `message`, `rule_id`, `rule`, cited evidence, clinical boundary, `next_step`, and `"This is a monitoring alert, not a diagnosis."`).
  - Never infers a diagnosis, fever, infection, hypoxia, arrhythmia, or immune/psychiatric condition from wearable telemetry or skin temperature (`TEMP-01`).
  - Explicitly treats `DATA-01` (`data_quality`) and `DATA-02` (`setup`) as non-physiological notices (`"infer no health event"`).
  - Returns `"I cannot answer that from my sources."` with `citations: []` when a question has no supporting evidence in `S1`–`S9`.

---

## 3. Commands (Run from Repository Root)

```bash
# Build/refresh rag/index/corpus.json and rag/index/meta.json (9 documents)
python -m rag.ingest

# Run the 10 grounding & accuracy benchmark questions (deterministic retrieval_only mode)
python -m rag.test_10_questions

# Run the 10 grounding questions using local Ollama (llm mode with fallback)
python -m rag.test_10_questions --llm
```
