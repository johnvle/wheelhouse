#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check for .env
if [ ! -f "$ROOT_DIR/.env" ]; then
  echo "ERROR: .env file not found. Copy .env.example and fill in your credentials."
  exit 1
fi

# --- Backend setup ---
cd "$ROOT_DIR/backend"

if [ ! -d ".venv" ]; then
  echo "Creating Python virtual environment..."
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

echo "Running database migrations..."
alembic upgrade head

echo "Starting backend (http://localhost:8000)..."
uvicorn app.main:app --reload &
BACKEND_PID=$!

# --- Frontend setup ---
cd "$ROOT_DIR/frontend"

if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo "Starting frontend (http://localhost:5173)..."
npm run dev &
FRONTEND_PID=$!

# --- Cleanup on exit ---
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  wait $BACKEND_PID 2>/dev/null
  wait $FRONTEND_PID 2>/dev/null
  echo "Done."
}
trap cleanup EXIT INT TERM

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

wait
