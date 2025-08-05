#!/bin/bash
set -e

echo "🛠️ Running database migrations..."
alembic upgrade head

echo "🚀 Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 80 --workers 4 --reload
