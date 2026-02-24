#!/bin/bash
# ESG Dashboard Backend - Start Script

set -euo pipefail

# Navigate to backend directory
cd "$(dirname "$0")"

# Activate virtual environment if exists
if [ -d "../.venv" ]; then
    # shellcheck source=/dev/null
    source ../.venv/bin/activate
elif [ -d "venv" ]; then
    # shellcheck source=/dev/null
    source venv/bin/activate
fi

echo "Starting ESG Dashboard API Server..."
echo "API Docs: http://localhost:8000/docs"
echo "Health:   http://localhost:8000/"
echo ""

# Use app.main as default entrypoint (lighter than backend/main.py in dev).
# Exclude transient backup files from reload watch to avoid unnecessary restarts.
uvicorn app.main:app \
  --reload \
  --reload-exclude "app/services/*backup*.py" \
  --host 0.0.0.0 \
  --port 8000
