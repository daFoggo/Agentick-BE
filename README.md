# Agentick Backend

Agentick Backend is the FastAPI service for the Agentick project management platform. It owns authentication, team/project/task APIs, scheduling, AI-assisted task analysis, and agent outreach workflows.

## Tech Stack

| Area | Technology |
| --- | --- |
| API | FastAPI, Uvicorn |
| Data | PostgreSQL, SQLAlchemy 2, Alembic |
| Validation | Pydantic, pydantic-settings |
| Auth | JWT, Argon2 password hashing |
| AI runtime | OpenRouter strategy layer, Opik tracing |
| Background jobs | APScheduler |
| Vector service | Qdrant |
| Tooling | uv, Ruff, pytest, Docker Compose |

## Getting Started

Install prerequisites:

- Docker Desktop
- Python 3.12+
- uv

Create local env files:

```bash
cp .env.example .env
```

Run the full local stack:

```bash
docker compose up -d --build
docker exec agentick-be-api alembic upgrade head
```

The API runs at:

- API: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`
- PostgreSQL host port: `5433`
- Qdrant: `http://localhost:6333`

Run the API locally without Docker for the app process:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Run the Opik agent playground locally:

```bash
uv run opik endpoint --project "Agentick" -- uv run uvicorn app.main:app --port 8000 --reload
```

## Common Commands

| Task | Command |
| --- | --- |
| Start stack | `docker compose up -d --build` |
| Stop stack | `docker compose down` |
| View API logs | `docker logs -f agentick-be-api` |
| Create migration | `docker exec agentick-be-api alembic revision --autogenerate -m "message"` |
| Apply migration | `docker exec agentick-be-api alembic upgrade head` |
| Run tests | `uv run pytest` |
| Lint and fix | `uv run ruff check . --fix` |
| Format | `uv run ruff format .` |

## Project Structure

```text
app/
├── api/v1/endpoints/   # FastAPI route handlers and dependency wiring
├── agents/             # LLM strategy and custom agent runtime
├── core/               # config, database, dependencies, security, scheduler
├── db/                 # session helpers
├── model/              # SQLAlchemy models
├── repository/         # persistence layer and UnitOfWork
├── schema/             # Pydantic request/response schemas
├── services/           # business orchestration
├── tools/              # LLM tool definitions and execution adapters
└── utils/              # shared utilities
migrations/             # Alembic revisions
tests/                  # pytest suite
```

## Documentation

The canonical development handbook is in `docs/handbook`.

| Document | Purpose |
| --- | --- |
| [00_index.md](docs/handbook/00_index.md) | Start here. Maps the backend handbook. |
| [01_project_overview.md](docs/handbook/01_project_overview.md) | Runtime, stack, and local setup. |
| [02_architecture.md](docs/handbook/02_architecture.md) | Layer boundaries and dependency direction. |
| [03_feature_development.md](docs/handbook/03_feature_development.md) | Standard flow for adding backend features. |
| [04_api_repository_service.md](docs/handbook/04_api_repository_service.md) | Endpoint, service, repository, response, and error patterns. |
| [05_ai_agent_runtime.md](docs/handbook/05_ai_agent_runtime.md) | AI agent, LLM strategy, tools, scheduler, and observability rules. |
| [06_quality_rules.md](docs/handbook/06_quality_rules.md) | Quality, migrations, tests, and review rules. |
| [07_development_checklist.md](docs/handbook/07_development_checklist.md) | Checklist before finishing backend work. |

## External References

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [uv](https://docs.astral.sh/uv/)
- [Ruff](https://docs.astral.sh/ruff/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [Qdrant](https://qdrant.tech/documentation/)
- [Opik](https://www.comet.com/docs/opik/)
