#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running database migrations..."
alembic upgrade head

# Check if RELOAD is set to true
RELOAD_FLAG=""
if [ "$RELOAD" = "true" ]; then
    echo "Hot reload is ENABLED"
    RELOAD_FLAG="--reload"
else
    echo "Hot reload is DISABLED"
fi

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} $RELOAD_FLAG
