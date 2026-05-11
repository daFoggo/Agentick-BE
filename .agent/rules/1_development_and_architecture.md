# 🏗️ Development & Architecture Rules

This guide defines the architectural standards, development patterns, and code quality guidelines for the **Agentick Backend** repository. Every AI Agent or developer working on this codebase must strictly adhere to these rules.

---

## 1. Overall Architecture & Base Patterns

### 1.1. Modular Monolith Architecture
The system operates as a **Modular Monolith**. All code runs within a single deployment unit but must remain logically and physically decoupled via clean directory structures (`app/repository`, `app/services`, `app/agents`). This ensures high data consistency while guaranteeing that components (e.g., the AI Agent Core) can be extracted into standalone Microservices later if scale dictates.

### 1.2. Repository & Service Layer Pattern
We enforce a strict separation between data access and business orchestration:
- **Repository Layer (`app/repository/`)**: Inherits from `BaseRepository`. Its exclusive goal is to hide implementation complexities of SQLAlchemy from the rest of the application. Services should interact solely with abstract persistence methods.
- **Service Layer (`app/services/`)**: Inherits from `BaseService`. Contains purely core business rules and coordinates between multiple repositories and AI outreach actions.

### 1.3. Project Directory Structure (Separation of Concerns)
Code must be organized strictly according to these designated layers:

* **`app/api/v1/endpoints/`**: Handles HTTP requests, validation, dependency injection wiring, and standard JSON response formatting.
* **`app/services/`**: Core business logic engine and agent workflow coordination.
* **`app/repository/`**: Data persistence and SQL concealment logic.
* **`app/model/`**: Declarative SQLAlchemy Database entities.
* **`app/schema/`**: Pydantic DTOs for request validation and response serialization.
* **`app/agents/`**: AI Reasoning loops, core prompt engineering, and LLM client abstraction.
* **`app/tools/`**: ReAct-based tool execution map and interface schemas for LLM interaction.
* **`app/core/`**: App-wide orchestration: configs, DB sessions, utility dependencies, and lifespan setup.
* **`migrations/`**: Alembic revision history.

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

---

## 5. Advanced Design Patterns

To maintain strict adherence to **Clean Architecture**, implementation of these patterns is mandatory:

### 5.1. Unit of Work (UoW) Pattern
Ensures transaction atomicity when multiple related repositories must be written to the database as a single batch (e.g., Atomic Registration flow).
- **Location**: `app/repository/unit_of_work.py`
- **Usage**: Always wrap multi-repository operations within a `with UnitOfWork(session_factory) as uow:` context manager. If an error occurs, everything automatically rolls back.

### 5.2. Dependency Injection (DI) Pattern
Utilize FastAPI's `Depends()` heavily to inject database sessions and services into routers. This abstracts resource life-cycles from core business handlers.
- **Location**: `app/core/dependencies.py`
- **Example**:
  ```python
  def get_current_user(db: Session = Depends(get_db)) -> User:
      # Automatically borrows session and handles post-request cleanup
      pass
  ```

### 5.3. Lifespan Pattern
Controls startup and shutdown lifecycle logic for the backend server to cleanly initialize and terminate background processes such as schedulers.
- **Location**: `app/main.py`
- **Implementation**: Must utilize `@asynccontextmanager` lifespan on the FastAPI instance to `start_scheduler()` and `shutdown_scheduler()` safely, preventing background thread resource leaks.
