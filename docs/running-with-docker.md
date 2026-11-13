# Running with Docker (optional)

Docker is a second way to run the app. `scripts/run_local.sh` and `.bat` remain the main path.

## Layout
- `docker-compose.yml` (repo root) starts the services.
- `backend/Dockerfile` and `backend/.dockerignore` build the backend image (context `./backend`).
- `frontend/Dockerfile` and `frontend/.dockerignore` build the frontend image (context `./frontend`).

The backend image contains only the backend code. Compose mounts `contract/`, `data/sample/`,
`data/runtime/` and `rag/` from the repo into the container, so edits to Sofia's CSV, Cesar's
`rag/ask.py` or the rules show up without rebuilding the data. `docker run` on its own will not
find those folders; always start it with `docker compose`.

If Cesar's `rag/ask.py` needs extra Python packages (PyMuPDF, sentence-transformers, FAISS),
add them to `backend/requirements.txt` and rebuild, because `ask()` runs inside the backend container.

## Windows
1. Install Docker Desktop (needs WSL 2; reboot if asked) and start it once.
2. In PowerShell, from the repo root: `docker compose up --build`
3. Open http://localhost:8000/api/status
No Docker? Use `scripts\run_local.bat` (needs Python 3.10 or newer).

## macOS / Linux
`./scripts/run_docker.sh` or `./scripts/run_local.sh`

## With the frontend
`docker compose --profile full up --build`, then open http://localhost:3000.
`NEXT_PUBLIC_*` values are baked in at build time, so changing them means rebuilding.
For daily frontend work Abdullah should still use `npm run dev`.

## Offline demo checklist
- Build while online (`docker compose build`), then confirm `docker compose up` works with Wi-Fi off.
- Ollama runs on the host (`ollama serve`), not in a container.
- The SQLite file is kept in `data/runtime/` on the host, so `reset_demo` and Docker share it.
- Never commit models, raw PDFs or the built index.
