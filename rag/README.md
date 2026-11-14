# RAG & Scientific Knowledge Library (`rag/`)

**Owner:** Cesar

Provides offline-capable source ingestion, indexing, evidence retrieval, clinical boundary enforcement, PC hardware capability detection, local LLM selection/downloading, and response generation (`llm` and `retrieval_only` modes) for `POST /api/assistant/ask` and `GET /api/status`.

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

## 2. PC Hardware Capability Detection & Model Selection

`rag/ask.py` includes a zero-dependency hardware capability detector (`detect_hardware()`) that inspects your machine's **total RAM, available free RAM, CPU logical cores, free disk space, and dedicated GPU VRAM** (across Windows, Linux, and macOS) and automatically selects or recommends an appropriate local LLM tier.

### Supported Model Tiers (`MODEL_CATALOG`)

| Tier | Hardware Requirement | Default Standalone GGUF (`./models/`) | Default Ollama Tag | Approx. Size |
|---|---|---|---|---|
| **`nano`** | `>= 2.0 GB` free RAM (basic CPU) | `qwen2.5-0.5b-instruct-q4_k_m.gguf` | `qwen2.5:0.5b` | ~398 MB |
| **`small`** | `>= 4.5 GB` free RAM (standard laptop) | `qwen2.5-1.5b-instruct-q4_k_m.gguf` | `qwen2.5:1.5b` | ~1.1 GB |
| **`standard`** | `>= 8.0 GB` free RAM or `>= 4.0 GB` GPU VRAM | `qwen2.5-3b-instruct-q4_k_m.gguf` | `llama3.2:3b` | ~2.0 GB |
| **`off`** | `< 2.0 GB` free RAM (or manually disabled) | *None (`retrieval_only` fallback)* | *None* | 0 MB |

### Supported Local Backends (`RAG_LLM_BACKEND`)
1. **`gguf` *(default — no Ollama required)***: Loads `.gguf` model files directly in Python from `./models/` (or your configured `models_dir`) using `llama-cpp-python` (`pip install -r rag/requirements.txt`). Automatically falls back to `retrieval_only` if no `.gguf` file is downloaded yet.
2. **`auto`**: Checks hardware limits and tries available local engines in order:
   - Standalone **`.gguf` files** stored inside `./models/` (or configured `models_dir`).
   - Local **Ollama** server (`http://127.0.0.1:11434`), picking a model that fits your PC's tier.
   - Local **OpenAI-compatible server** (e.g., LM Studio / `llama-server` at `LOCAL_OPENAI_URL`).
   - Instant fallback to deterministic **`retrieval_only`** mode if no LLM is available or if free RAM is below 2.0 GB.
3. **`ollama`**: Uses only the local Ollama server.
4. **`openai`**: Uses a local OpenAI-compatible endpoint (`LOCAL_OPENAI_URL`, default `http://127.0.0.1:1234/v1`).
5. **`off`**: Forces `retrieval_only` mode without invoking any LLM.

---

## 3. Configuring & Downloading Models

You can inspect your PC's capabilities, download a model matching your hardware, and persist your configuration into `rag/index/meta.json` directly from the terminal.

### A. Interactive Setup & Download Wizard
```bash
python -m rag.ask --configure
```
This interactive wizard:
1. Scans your CPU, available RAM, disk space, and GPU VRAM.
2. Recommends the optimal model tier (`nano`, `small`, or `standard`) for your PC.
3. Lets you download the model directly into `./models/` (`.gguf` with progress bar) or via Ollama (`ollama pull`), and automatically registers downloaded `.gguf` files with Ollama if Ollama is installed.
4. Saves your chosen settings in `rag/index/meta.json`.

### B. Direct CLI Commands
```bash
# 1. Inspect PC hardware capabilities, installed models, and active settings
python -m rag.ask --check

# 2. Automatically download the best model for your PC's detected hardware
python -m rag.ask --download auto

# 3. Download a specific model tier (nano | small | standard) as a .gguf file into ./models/ (or a custom folder)
python -m rag.ask --download nano --backend gguf
python -m rag.ask --download small --backend gguf --models-dir D:/astro-models

# 4. Change the default models download/storage folder without downloading immediately
python -m rag.ask --models-dir ./models

# 5. Download a specific model tier via Ollama
python -m rag.ask --download small --backend ollama

# 6. Switch active model tier, backend, or preferred model without downloading
python -m rag.ask --set-tier nano
python -m rag.ask --backend gguf
python -m rag.ask --set-model qwen2.5-0.5b-instruct-q4_k_m.gguf

# 7. Disable LLM generation (force deterministic retrieval_only mode)
python -m rag.ask --backend off
```

> **Note on Standalone GGUF Execution (Without Ollama):**
> If you download a `.gguf` file into `./models/` and Ollama is running in `auto` mode, `rag/ask.py` registers the `.gguf` inside Ollama so both `/api/status` and `/api/assistant/ask` use it seamlessly. If you want to run `.gguf` files directly in Python **without** Ollama (`--backend gguf`), install the RAG requirements (which includes pre-built wheels for `llama-cpp-python` and `psutil`):
> ```bash
> pip install -r rag/requirements.txt
> ```

### C. Configuring the Models Download Directory (`--models-dir` / `RAG_MODELS_DIR`)

By default, `.gguf` models are downloaded into and loaded from `./models/` at the repository root (which is gitignored so large `.gguf` files are never committed). You can change this folder to any relative or absolute path (for example, another drive with more free space):

1. **Via CLI flag (persists in `rag/index/meta.json`):**
   ```bash
   # Save a new default folder for all future model downloads and lookups
   python -m rag.ask --models-dir D:/astro-models

   # Or specify the folder while downloading a model
   python -m rag.ask --download nano --backend gguf --models-dir D:/astro-models
   ```
2. **Via the Interactive Wizard (`python -m rag.ask --configure`):**
   Prompts for the destination folder before downloading (or under option `[3]`).
3. **Via Environment Variable (`.env` or shell):**
   ```env
   RAG_MODELS_DIR=D:/astro-models
   ```

**Resolution priority:** `--models-dir` CLI flag -> `RAG_MODELS_DIR` env var -> `llm_config.models_dir` in `rag/index/meta.json` -> `./models` default. Before downloading, `rag/ask.py` automatically checks available free disk space on the target drive.

### D. Environment Variable Overrides & `rag/index/meta.json` Schema
You can override settings via `.env` or shell environment variables:
- `RAG_LLM_BACKEND`: `auto` | `ollama` | `gguf` | `openai` | `off`
- `RAG_MODEL_TIER`: `auto` | `nano` | `small` | `standard` | `off`
- `RAG_MODELS_DIR`: Custom directory path where `.gguf` models are downloaded and loaded from (default `models`)
- `OLLAMA_MODEL`: Specific Ollama model tag (e.g., `qwen2.5:0.5b`, `llama3.2:3b`)
- `RAG_GGUF_MODEL`: Specific `.gguf` filename inside the configured models directory
- `OLLAMA_URL`: Ollama server URL (default `http://127.0.0.1:11434`)
- `LOCAL_OPENAI_URL`: OpenAI-compatible server URL (default `http://127.0.0.1:1234/v1`)
- `ASK_TIMEOUT_SECONDS`: Timeout in seconds before falling back to `retrieval_only` (default `20`)

Example `rag/index/meta.json` generated by `rag/ask.py` and `rag/ingest.py`:
```json
{
  "documents_indexed": 9,
  "source_ids": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"],
  "sources_enriched_from_disk": 9,
  "llm_config": {
    "backend": "gguf",
    "tier": "auto",
    "preferred_model": "",
    "models_dir": "models"
  },
  "hardware_detected": {
    "os": "Windows 10",
    "cpu_cores": 12,
    "ram_total_gb": 31.37,
    "ram_available_gb": 13.39,
    "gpu_name": "NVIDIA GeForce RTX 3080",
    "vram_gb": 10.0,
    "recommended_tier": "standard"
  }
}
```

---

## 4. Interface & Safety Boundaries (`rag/ask.py`)

`backend/app/services/rag_adapter.py` imports `rag.ask` automatically:

```python
ask(question: str, alert: dict | None = None, history: list[dict[str, str]] | None = None) -> dict
retrieval_only(question: str, alert: dict | None = None, history: list[dict[str, str]] | None = None) -> dict
```

- **Zero mandatory external dependencies**: Hardware detection, retrieval, and Ollama/OpenAI HTTP calls use Python's standard library only, so `rag/ask.py` runs inside `backend`'s existing environment and Docker container without internet access.
- **Multi-Turn Conversation Memory**: Supports optional `history` (`[{"role": "user"|"assistant", "content": "..."}]` or CLI `--history`) plus an in-process rolling memory (`_CONVERSATION_MEMORY`) so follow-up questions (e.g., *"What should I do next if it persists?"*) retain topic context from previous turns while still refusing out-of-scope queries.
- **Actionable Protocol Suggestions**: Every response includes concrete operational next steps (`Suggested next step: ...`) grounded in Ammara's protocol and EIMO workflows, both for alert-linked and free-text questions.
- **Automatic `rag/index/meta.json` creation**: Importing `rag.ask` ensures `rag/index/meta.json` (`{"documents_indexed": 9, ...}`) exists even on a fresh git clone where `rag/index/*` is gitignored.
- **Clinical & Wording Guardrails**:
  - Follows Section 4 alert explanation structure (`SEVERITY`, `message`, `rule_id`, `rule`, cited evidence, clinical boundary, `next_step`, and `"This is a monitoring alert, not a diagnosis."`).
  - Never infers a diagnosis, fever, infection, hypoxia, arrhythmia, or immune/psychiatric condition from wearable telemetry or skin temperature (`TEMP-01`).
  - Explicitly treats `DATA-01` (`data_quality`) and `DATA-02` (`setup`) as non-physiological notices (`"infer no health event"`).
  - Returns `"I cannot answer that from my sources."` with `citations: []` when a question has no supporting evidence in `S1`–`S9`.

---

## 5. Indexing & Verification Commands (Run from Repository Root)

```bash
# Build/refresh rag/index/corpus.json and rag/index/meta.json (9 documents + hardware profile)
python -m rag.ingest

# Check PC hardware capability and active LLM configuration
python -m rag.ask --check

# Run the 10 grounding & accuracy benchmark questions (deterministic retrieval_only mode)
python -m rag.test_10_questions

# Run the 10 grounding questions using the configured LLM (with automatic fallback)
python -m rag.test_10_questions --llm
```
