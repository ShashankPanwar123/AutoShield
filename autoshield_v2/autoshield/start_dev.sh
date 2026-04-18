#!/usr/bin/env bash
# ================================================================
# AutoShield — Local Development Startup
# Starts the FastAPI backend and Streamlit frontend in parallel.
# Usage: bash start_dev.sh
# ================================================================

set -e

echo ""
echo "  ┌─────────────────────────────────────┐"
echo "  │   AutoShield AI  —  Dev Server      │"
echo "  └─────────────────────────────────────┘"
echo ""

# Load .env if present
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  echo "  ✅ Loaded .env"
fi

# Ensure models dir exists
mkdir -p models data

echo "  🚀 Starting FastAPI backend on http://localhost:8000"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

echo "  🎨 Starting Streamlit frontend on http://localhost:8501"
BACKEND_URL=http://localhost:8000 streamlit run frontend/app.py &
FRONTEND_PID=$!

echo ""
echo "  Backend  → http://localhost:8000"
echo "  Frontend → http://localhost:8501"
echo "  API Docs → http://localhost:8000/docs"
echo ""
echo "  Press Ctrl+C to stop both servers."
echo ""

# Graceful shutdown
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '  Servers stopped.'" INT TERM
wait
