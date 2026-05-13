# Architecture

Agentick Backend is a modular monolith. It deploys as one FastAPI service, but code must stay separated by responsibility so individual domains can evolve without tight coupling.

## Dependency Direction

```text
app/api/v1/endpoints
  -> app/services
    -> app/repository
      -> app/model
```

Schemas, core dependencies, and utilities may be imported by the layers that need them, but business flow should still move through this direction.

## Layer Responsibilities

### Endpoints

`app/api/v1/endpoints/`

- Define routes, path/query/body parameters, and `response_model`.
- Select auth dependencies such as `get_current_active_user`.
- Wire services with FastAPI `Depends`.
- Wrap output in `ResponseSchema`.
- Avoid direct SQLAlchemy query logic.
- Avoid multi-step business workflows unless the endpoint is only coordinating existing service calls.

### Services

`app/services/`

- Own business rules.
- Check domain permissions after loading the required entities.
- Coordinate multiple repositories.
- Decide when a workflow needs `UnitOfWork`.
- Call AI, notification, email, or scheduler-facing logic when that is part of the use case.
- Raise `AppError` subclasses for expected failures.

### Repositories

`app/repository/`

- Own SQLAlchemy query details.
- Inherit `BaseRepository` when possible.
- Expose domain-specific query methods when base CRUD is not enough.
- Return ORM models or query result structures for services to use.
- Do not know about HTTP status codes, response envelopes, or FastAPI dependencies.

### Models

`app/model/`

- Define SQLAlchemy database entities.
- Inherit the shared base model.
- Keep persistence shape here, not request/response decisions.

### Schemas

`app/schema/`

- Define Pydantic request and response DTOs.
- Keep list/search input schemas near the domain schema.
- Use response schemas to prevent accidental leaking of internal ORM state.

### Core

`app/core/`

- Configuration, database setup, shared dependencies, auth/security helpers, middleware, exceptions, and scheduler lifecycle.

## Session Boundary

`get_db()` in `app/core/dependencies.py` yields the request database session. Endpoint service factories should pass that active session into repositories:

```python
repository = ProjectRepository(lambda: nullcontext(db))
```

This keeps all repositories used by one request aligned to the same session.

## Lifespan

Application startup and shutdown work belongs in the FastAPI lifespan context in `app/main.py`. Long-lived background jobs should be started through core lifecycle code, not at import time.
