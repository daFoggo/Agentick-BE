# API, Repository, And Service Patterns

## Response Envelope

Normal API endpoints return `ResponseSchema`.

```python
@router.post("", response_model=ResponseSchema[ProjectRead])
def create_project(...):
    result = service.create_project(schema, current_user)
    return ResponseSchema(data=result, message="Project created successfully")
```

Use raw dictionaries only for health/system endpoints where the response is intentionally outside the application envelope.

## List Responses

Use `FindResult[T]` for paginated or searchable list responses.

```python
@router.get("", response_model=ResponseSchema[FindResult[ProjectRead]])
def get_projects(find_query: ProjectFind = Depends(), ...):
    result = service.get_projects(find_query, current_user)
    return ResponseSchema(data=result)
```

Repository list methods should return the shape expected by `FindResult`:

```python
{
    "founds": items,
    "search_options": {
        "page": page,
        "page_size": page_size,
        "ordering": ordering,
        "total_count": total_count,
    },
}
```

## Dependency Wiring

Endpoint modules own service factories.

```python
def get_project_service(db=Depends(get_db)) -> ProjectService:
    project_repository = ProjectRepository(lambda: nullcontext(db))
    return ProjectService(project_repository=project_repository, ...)
```

Do not instantiate request services at module import time. They depend on the request session.

## Error Pattern

Expected application failures use `AppError` subclasses:

- `DuplicatedError` -> 400
- `AuthError` -> 401
- `NotFoundError` -> 404
- `ValidationError` -> 422

Use these instead of ad hoc `HTTPException` unless a new error class is needed.

## Base Repository

`BaseRepository` provides common CRUD and list behavior. Domain repositories should add only query methods that cannot be expressed clearly through the base behavior.

Rules:

- Query logic belongs here.
- HTTP response shape does not.
- Business authorization does not.
- SQLAlchemy relationships/eager loading details belong here or on the model.

## Base Service

`BaseService` is a thin CRUD wrapper. Domain services should add named methods for real use cases.

Good:

```python
service.update_project(project_id, schema, current_user)
```

Weak:

```python
service.patch(project_id, schema)
```

Use the explicit domain method when permissions, soft delete, side effects, or multi-repository work are involved.

## Unit Of Work

Use `UnitOfWork` when one action writes multiple repositories and must commit or rollback together.

```python
with UnitOfWork(self._repository.session_factory) as uow:
    project = uow.projects.create(schema, auto_commit=False)
    uow.project_members.create(..., auto_commit=False)
```

Do not manually commit inside a `UnitOfWork` block. Let the context manager commit on success and rollback on failure.
