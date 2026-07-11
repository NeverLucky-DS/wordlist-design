#!/usr/bin/env sh
# Container entrypoint: bring the database schema up to date, then serve the API.
# Schema is owned by Alembic (backend/alembic/) — this is what replaces the old
# create_all()/ALTER-TABLE-on-startup hack.
set -e

echo "→ Applying database migrations (alembic upgrade head)…"
alembic upgrade head

echo "→ Starting API on :8000 (uvicorn)…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
