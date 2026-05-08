# 🏗️ Development & Architecture Rules

This guide defines the architectural standards, development patterns, and code quality guidelines for the **Agentick Backend** repository. Every AI Agent or developer working on this codebase must strictly adhere to these rules.

---

## 1. Clean Architecture Pattern

Agentick-BE follows the **Clean Architecture** pattern to separate concerns and improve maintainability. Code must be organized into the following layers:

* **`app/api/v1/endpoints/`**: Handles HTTP requests, input validation via schemas, dependency injection wiring, and standard response formatting.
* **`app/services/`**: Implements core business logic, orchestrates transactions, coordinates between repositories, and triggers proactive agent outreach. Inherits from `BaseService`.
* **`app/repository/`**: Handles database access, queries, and persistence using SQLAlchemy. Inherits from `BaseRepository`.
* **`app/model/`**: Defines database tables using SQLAlchemy Declarative Style. Inherits from `BaseModel`.
* **`app/schema/`**: Defines data validation, serialization, and deserialization using Pydantic models.
* **`app/agents/`**: Contains core AI Agent reasoning loops, ReAct engine, LLM prompting, and copywriting logic.
* **`app/tools/`**: Implements computer-interface adapters, function schemas, and tool execution maps for the AI Agent.
* **`app/core/`**: Manages system-wide configurations, database sessions, security (JWT/Hashing), and core dependencies.
* **`migrations/`**: Contains historical database schema changes managed by Alembic.

---

## 2. Standard 7-Step Development Pattern

When adding any new feature, always follow this strict sequence:

1. **Define Database Model**: Create the table structure in `app/model/` (must inherit from `BaseModel` in `base_model.py`).
2. **Define Pydantic Schemas**: Create validation and serialization classes for Input/Output in `app/schema/`.
3. **Implement Repository**: Create a dedicated repository class in `app/repository/` (must inherit from `BaseRepository` in `base_repository.py`).
4. **Implement Service**: Write core business logic in `app/services/` (must inherit from `BaseService` in `base_service.py`).
5. **Create API Endpoint**: Define routes, request methods, and inputs in `app/api/v1/endpoints/`.
6. **Setup Dependency Injection**: Implement a `get_<feature>_service` function in the endpoint file to wire dependencies.
7. **Generate & Apply Migration**:
   * Generate: `docker exec agentick-be-api alembic revision --autogenerate -m "Add feature name"`
   * Apply: `docker exec agentick-be-api alembic upgrade head`

---

## 3. Standard API Response Format

Every API endpoint must return a structured response adhering to this format:

```json
{
  "success": true,
  "message": "Information message description",
  "data": { ... }
}
```

Do not return raw objects or unstructured dictionaries. Always wrap responses in a standard `ResponseSchema`.

---

## 4. Code Quality & Formatting (Ruff)

We use **Ruff** for high-performance linting, formatting, and auto-fixing. Before committing or pushing code, the following commands are **mandatory**:

### Check & Auto-Fix Errors
```bash
uv run ruff check . --fix
```

### Format Code
```bash
uv run ruff format .
```

### ⚠️ Special Rule for SQLAlchemy Queries in Ruff
Ruff's `E712` linter rule warns against using `== False` or `== True` for boolean checks. However, in SQLAlchemy, direct comparison is required to build the correct SQL query tree.
* **Correct (Ruff-compliant & SQLAlchemy-safe)**: Use `.is_(False)` or `.is_(True)`.
  ```python
  # Do this:
  query = session.query(Task).filter(Task.is_deleted.is_(False))
  ```
* **Incorrect**:
  ```python
  # Do NOT do this:
  query = session.query(Task).filter(Task.is_deleted == False)  # Causes Ruff E712
  query = session.query(Task).filter(not Task.is_deleted)       # Breaks SQLAlchemy query tree
  ```
