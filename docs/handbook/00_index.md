# Backend Handbook

This handbook is the source of truth for Agentick Backend development patterns. It intentionally focuses on engineering rules and does not try to document every model, endpoint, or business flow.

## Reading Order

1. [Project Overview](01_project_overview.md)
2. [Architecture](02_architecture.md)
3. [Feature Development](03_feature_development.md)
4. [API, Repository, And Service Patterns](04_api_repository_service.md)
5. [AI Agent Runtime](05_ai_agent_runtime.md)
6. [Quality Rules](06_quality_rules.md)
7. [Development Checklist](07_development_checklist.md)

## Core Decisions

- The backend is a modular monolith.
- The main dependency direction is endpoint -> service -> repository -> model.
- FastAPI dependency injection wires request-scoped sessions and services.
- API responses use `ResponseSchema`.
- SQLAlchemy access is hidden behind repositories.
- Business orchestration lives in services.
- Multi-repository writes use `UnitOfWork`.
- LLM access goes through the strategy layer.
- Scheduler work belongs in `app/core/scheduler.py`.
- Alembic is required for schema changes.

## What Not To Add Here

- Full database model catalogs.
- ERD dumps.
- Product requirement docs.
- Backend implementation history.
- Long business flow descriptions that duplicate code.

Those documents get stale quickly. Keep the handbook focused on patterns that guide future development.
