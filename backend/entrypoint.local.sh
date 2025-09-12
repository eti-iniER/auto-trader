#!/bin/bash
set -e

echo "🛠️ Running database migrations..."
uv run alembic upgrade head

echo "🚀 Starting FastAPI server..."
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 80 --workers 4 --reload --log-level trace
