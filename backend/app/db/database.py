from __future__ import annotations

import sqlite3
from pathlib import Path

from app import config

CORE_TEMPERATURE_SQL = Path(__file__).with_name("core_temperature.sql")


def connect() -> sqlite3.Connection:
    path = config.db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def db_exists() -> bool:
    return config.db_path().exists()


def get_db():
    """FastAPI dependency: one connection per request."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def ensure_core_table(conn: sqlite3.Connection) -> None:
    """Create the manual core-temperature table if it is missing (safe to call every start)."""
    conn.executescript(CORE_TEMPERATURE_SQL.read_text(encoding="utf-8"))
