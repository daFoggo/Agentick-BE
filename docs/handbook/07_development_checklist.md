# Development Checklist

Use this checklist before finishing backend work.

## Architecture

- Endpoint imports service, not repository internals unless wiring dependencies.
- Service owns business logic and permission checks.
- Repository owns SQLAlchemy details.
- Schema owns validation and serialization.
- Core shared dependencies are in `app/core`.

## API

- Endpoint has `response_model`.
- Normal endpoint returns `ResponseSchema`.
- Authenticated routes use the right current-user dependency.
- Expected failures raise `AppError` subclasses.
- List endpoints use `FindResult` when returning searchable/paginated results.

## Persistence

- Schema changes have Alembic migrations.
- Migration was reviewed for accidental drops or unrelated changes.
- Soft-delete reads filter deleted records.
- Boolean filters use `.is_(True)` / `.is_(False)`.
- Multi-repository writes use `UnitOfWork` when atomicity matters.

## AI And Background Work

- Deterministic checks happen before LLM calls.
- LLM provider calls go through the strategy layer.
- Tool schemas are explicit and validate important fields.
- Scheduler work does not start at import time.
- Background jobs use safe session boundaries.

## Verification

Run the smallest useful checks for the change:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

For docs-only changes, `git diff --check` is usually enough.
