#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# Kill any process already listening on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

# Activate venv and start the API
source .venv/bin/activate
exec uvicorn mediaparty_trust_api.main:app --port 8000 --reload
