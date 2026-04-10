#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

API_PID=""
WORKER_PID=""
WEB_PID=""

cleanup() {
  echo ""
  echo "Shutting down..."
  [ -n "$WEB_PID" ] && kill "$WEB_PID" 2>/dev/null
  [ -n "$WORKER_PID" ] && kill "$WORKER_PID" 2>/dev/null
  [ -n "$API_PID" ] && kill "$API_PID" 2>/dev/null
  echo "Done."
  exit 0
}

trap cleanup SIGINT SIGTERM

echo "==============================="
echo "  Magnet Local Dev"
echo "==============================="
echo ""

# 1. Start infra
echo "[1/5] Starting infra (Postgres, Redis, MinIO)..."
docker compose up -d postgres redis minio
echo "  Waiting for Postgres..."
until docker compose exec -T postgres pg_isready -U magnet -d magnet >/dev/null 2>&1; do
  sleep 1
done
echo "  Postgres ready."

# 2. Load env
set -a
source .env
set +a

# 3. Install deps if needed
echo "[2/5] Checking dependencies..."
if [ ! -d "packages/api/.venv" ]; then
  echo "  Installing API dependencies..."
  (cd packages/api && uv sync)
fi
if [ ! -d "packages/web/node_modules" ]; then
  echo "  Installing Web dependencies..."
  (cd packages/web && npm install)
fi

# 4. Run migrations
echo "[3/5] Running database migrations..."
(cd packages/api && uv run alembic upgrade head)

# 5. Start services
echo "[4/5] Starting API server..."
(cd packages/api && uv run uvicorn app.main:app --reload --port 8000) &
API_PID=$!

echo "[5/5] Starting Celery worker..."
(cd packages/api && uv run celery -A app.worker worker --loglevel=info) &
WORKER_PID=$!

sleep 2

echo ""
echo "==============================="
echo "  All services running"
echo ""
echo "  Web:   http://localhost:3000"
echo "  API:   http://localhost:8000"
echo "  MinIO: http://localhost:9001"
echo "         (admin: minioadmin / minioadmin)"
echo ""
echo "  Press Ctrl+C to stop all"
echo "==============================="
echo ""

echo "Starting Web dev server..."
(cd packages/web && npm run dev) &
WEB_PID=$!

wait
