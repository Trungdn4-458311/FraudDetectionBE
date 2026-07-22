#!/usr/bin/env bash
# Serve the Streamlit review queue (default) or the FastAPI scorer (`api`).
set -e
MODE="${1:-app}"
if [ "$MODE" = "api" ]; then
    exec uvicorn api:app --host 0.0.0.0 --port "${PORT:-8000}"
else
    exec streamlit run app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0
fi
