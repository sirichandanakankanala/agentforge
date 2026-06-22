#!/usr/bin/env bash
set -euo pipefail

# Simple dev runner for AgentForge
# Assumptions: you have activated your conda env (agentforge) and installed deps.
# Usage: from repo root: `bash run-dev.sh`

ROOT="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

echo "Starting backend (uvicorn) -> $LOG_DIR/backend.log"
(cd "$ROOT/backend" && nohup python -m uvicorn main:app --reload --port 8000 >"$LOG_DIR/backend.log" 2>&1 &) 

echo "Starting frontend (Vite) -> $LOG_DIR/frontend.log"
(cd "$ROOT/frontend" && nohup npm run dev >"$LOG_DIR/frontend.log" 2>&1 &) || echo "Frontend may need an interactive terminal; check $LOG_DIR/frontend.log"

echo "Starting Streamlit -> $LOG_DIR/streamlit.log"
nohup streamlit run "$ROOT/backend/streamlit_app.py" --server.port 8501 >"$LOG_DIR/streamlit.log" 2>&1 &

echo "All services started (background). Logs: $LOG_DIR"
echo "If a service fails (frontend often needs a terminal), run it manually in its own terminal:" 
echo "  cd backend && python -m uvicorn main:app --reload --port 8000"
echo "  cd frontend && npm run dev"
echo "  streamlit run backend/streamlit_app.py --server.port 8501"
