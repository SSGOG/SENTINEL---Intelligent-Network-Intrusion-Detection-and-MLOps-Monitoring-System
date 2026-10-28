#!/usr/bin/env bash
set -e

# Start FastAPI backend in background
uvicorn src.sentinel.api:app --host 0.0.0.0 --port 8000 &

# Start Streamlit frontend (foreground)
# Adjust the path to the main Streamlit script if different
streamlit run src/sentinel/dashboard.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true