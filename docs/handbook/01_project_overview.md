# Project Overview

Agentick Backend is the API and AI runtime service for the Agentick product. It provides authentication, team/project/task management, scheduling, notifications, calendar/event integration, and AI-assisted project workflows.

## Runtime

- Python 3.12+
- FastAPI application in `app/main.py`
- API v1 router mounted at `settings.API_V1_STR`, currently `/api/v1`
- PostgreSQL via SQLAlchemy
- Alembic migrations in `migrations/`
- APScheduler started and stopped through FastAPI lifespan
- Qdrant available in Docker Compose for vector workflows
- OpenRouter and Opik used by AI agent workflows

## Environment

Configuration lives in `app/core/config.py` and uses `pydantic-settings`.

Load order:

1. `.env`
2. `.env.{ENV}` when present

Important local values:

```env
ENV=dev
DATABASE_URL=postgresql://agentick_user:agentick_password@db:5432/agentick_db
SECRET_KEY=...
FRONTEND_URL=http://localhost:3000
OPENROUTER_API_KEY=...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
```

## Local Development

Docker path:

```bash
docker compose up -d --build
docker exec agentick-be-api alembic upgrade head
```

Local app process:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Agent playground:

```bash
uv run opik endpoint --project "Agentick" -- uv run uvicorn app.main:app --port 8000 --reload
```

## Checks

Use focused checks for the work being done:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

Docs-only changes do not require Ruff or pytest unless requested.
