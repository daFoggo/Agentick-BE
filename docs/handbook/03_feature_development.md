# Feature Development

Use this flow when adding or refactoring backend features.

## Standard Sequence

1. Define or update the SQLAlchemy model in `app/model/`.
2. Define Pydantic schemas in `app/schema/`.
3. Add repository methods in `app/repository/`.
4. Add service methods in `app/services/`.
5. Add endpoints in `app/api/v1/endpoints/`.
6. Register the router in `app/api/v1/routes.py`.
7. Generate and review an Alembic migration if the schema changed.
8. Add focused tests when behavior or permissions change.

## Endpoint Checklist

- Use `APIRouter(prefix=..., tags=[...])`.
- Set `response_model=ResponseSchema[...]`.
- Use `Depends(get_current_active_user)` when authentication is required.
- Wire services through `get_<feature>_service`.
- Return `ResponseSchema(data=..., message=...)`.
- Keep request parsing and HTTP concerns in the endpoint.

## Service Checklist

- Put business behavior here.
- Keep permission checks close to the data they require.
- Raise `AuthError`, `NotFoundError`, `DuplicatedError`, or `ValidationError` for expected failures.
- Use repository methods for persistence.
- Use `UnitOfWork` for atomic multi-repository writes.
- Keep LLM calls behind the relevant agent/service abstraction.

## Repository Checklist

- Inherit `BaseRepository` when the domain maps to one model.
- Add explicit query methods for domain-specific reads.
- Use `.is_(False)` or `.is_(True)` for SQLAlchemy boolean filters.
- Keep soft-delete filtering consistent for soft-deleted domains.
- Do not return response envelopes from repositories.

## Migration Checklist

Create migration:

```bash
docker exec agentick-be-api alembic revision --autogenerate -m "Describe change"
```

Review the generated file before keeping it:

- No unrelated table churn.
- No accidental drops.
- Constraints and indexes match the model change.
- Downgrade is reasonable for the migration style already used in the repo.

Apply migration:

```bash
docker exec agentick-be-api alembic upgrade head
```
