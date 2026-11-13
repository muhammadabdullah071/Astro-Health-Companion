#!/usr/bin/env bash
# Needs Docker Desktop (Windows/macOS) or Docker Engine (Linux).
cd "$(dirname "$0")/.."
docker compose up --build "$@"
