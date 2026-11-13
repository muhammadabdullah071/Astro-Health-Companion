"""Astro-Health Companion API, contract v1.

Run from the backend folder:  uvicorn app.main:app --host 127.0.0.1 --port 8000
The database is created and seeded automatically on first start.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.db import database, seed
from app.errors import register_error_handlers
from app.routes import alerts, assistant, profile, readings, status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("astro")


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not database.db_exists():
        logger.info("No database found, seeding: %s", seed.seed())
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Astro-Health Companion API", version="1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins(),
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    for router in (status.router, profile.router, readings.router, alerts.router, assistant.router):
        app.include_router(router, prefix="/api")
    return app


app = create_app()
