from fastapi import APIRouter

from app import config
from app.db import database
from app.services import health

router = APIRouter()


@router.get("/status")
def get_status():
    backend, last_update = "ok", None
    try:
        conn = database.connect()
        try:
            conn.execute("SELECT 1")
            last_update = conn.execute("SELECT MAX(ts) FROM readings").fetchone()[0]
        finally:
            conn.close()
    except Exception:
        backend = "error"
    return {
        "backend": backend,
        "offline_mode": config.offline_mode(),
        "llm": "ready" if health.probe_llm() else "unavailable",
        "documents_indexed": health.documents_indexed(),
        "last_data_update": last_update,
        "data_label": config.DATA_LABEL,
    }
