# Agentick Backend

Agentick is an AI Agent-powered project management platform that proactively detects deadline risks and improves deadline estimation over time using accumulated execution behavior data.

---

## 🚀 Installation & Setup

If you are starting from scratch (no dev tools installed), follow step 0. Otherwise, skip to step 1.

### 0. Prerequisites & Environment Setup

You need to install these tools to run the project locally:

1. **Git**: To download the source code.
   - [Download for Windows/Mac/Linux](https://git-scm.com/downloads)
   - Verify: Open your terminal and run `git --version`

2. **Docker Desktop**: To run the Database and API container smoothly.
   - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - *Make sure Docker is running before moving to the next steps.*

3. **Astral UV**: Our high-speed Python manager (needed for AI tools and code linting).
   - **Windows (PowerShell):** 
     ```powershell
     powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
     ```
   - **macOS/Linux:** 
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Restart terminal and verify: `uv --version`

---

### 1. Clone the Repository
Open your terminal (PowerShell, CMD, or Terminal) and run:
```bash
git clone https://github.com/daFoggo/Agentick-BE.git
cd Agentick-BE
```

### 2. Environment Configuration
Create a `.env` file in the root folder of the project. Copy and paste the following content:
```env
# Database Credentials
POSTGRES_USER=agentick_user
POSTGRES_PASSWORD=agentick_password
POSTGRES_DB=agentick_db
DATABASE_URL=postgresql://agentick_user:agentick_password@db:5432/agentick_db

# Security
SECRET_KEY=your_super_secret_key
ENV=dev

# AI Agent & Observability (Required for AI features)
OPENROUTER_API_KEY=your_key_here
OPIK_API_KEY=your_key_here
OPIK_WORKSPACE=your_workspace
```
> [!IMPORTANT]
> Never commit the `.env` file to version control.

### 3. Starting the System with Docker
Run this command to download dependencies and start the system:
```bash
docker compose up -d --build
```
*Wait 10-15 seconds for the PostgreSQL database to fully initialize.*

### 4. Database Migrations (Alembic)
The database starts empty. Run this command to create all tables and schemas:
```bash
docker exec agentick-be-api alembic upgrade head
```

### 5. AI Agent Playground & Local Running
Our backend features an intelligent AI Agent, monitored via Opik.
To enable the **Opik Agent Playground** with live local pairing and reload, run:
```bash
uv run opik endpoint --project "Agentick" -- uv run uvicorn app.main:app --port 8000 --reload
```

**Result:** Your API is now live at `http://localhost:8000/docs`.


---


## 🛠 Maintenance Commands

| Action | Command |
| :--- | :--- |
| **Check Logs** | `docker logs -f agentick-be-api` |
| **Create Migration** | `docker exec agentick-be-api alembic revision --autogenerate -m "description"` |
| **Apply Migration** | `docker exec agentick-be-api alembic upgrade head` |
| **Reset Database** | `docker compose down -v` (⚠️ Deletes all data) |

---

## 📐 Project Structure

Agentick-BE follows the **Clean Architecture** pattern to separate concerns and improve maintainability.

### Folder Breakdown
- `app/api/v1/endpoints/`: Handles HTTP requests, input validation, and formatting responses.
- `app/services/`: Contains core business logic, cross-repository coordination, and proactive agent outreach.
- `app/repository/`: Handles data access and SQLAlchemy queries (Inherits from `base_repository.py`).
- `app/model/`: Defines database tables using SQLAlchemy (Inherits from `base_model.py`).
- `app/schema/`: Defines data validation and serialization using Pydantic.
- `app/agents/`: AI Agent core reasoning loops, LLM interaction, and copywriting.
- `app/tools/`: Adapters and external function definitions/execution mapping for LLM.
- `app/core/`: System-wide configurations (Security, Database, Dependencies).
- `app/utils/`: Shared helper utilities (Hashing, Email sender, Qdrant helper, Query builders).
- `migrations/`: Historical records of database schema changes managed by Alembic.

### Data Flow Example
When a client requests `POST /api/v1/auth/sign-in`:
1. **Router**: Receives the request in `app/api/v1/endpoints/auth.py`.
2. **Dependency**: A specific `get_auth_service` function instantiates the service and its required repositories.
3. **Service**: `AuthService` performs logic (e.g., matching hashed passwords).
4. **Repository**: `UserRepository` fetches raw data from PostgreSQL.
5. **Response**: The Service returns the result, which the endpoint wraps in a standardized `ResponseSchema`.

---

## 🏗 Development Pattern

To maintain a consistent codebase, follow these steps when adding a new feature:

1.  **Define Model**: Create the table structure in `app/model/` (kế thừa `BaseModel` từ `base_model.py`).
2.  **Define Schemas**: Create Pydantic classes for Input/Output in `app/schema/`.
3.  **Implement Repository**: Create a repository in `app/repository/` (kế thừa `BaseRepository` từ `base_repository.py`).
4.  **Implement Service**: Write business logic in `app/services/`.
5.  **Create Endpoint**: Define routes in `app/api/v1/endpoints/`.
6.  **Setup Injection**: Implement a `get_<feature>_service` function in the endpoint file to wire dependencies.
7.  **Migration**: 
    - Generate: `docker exec agentick-be-api alembic revision --autogenerate -m "Add feature name"`
    - Apply: `docker exec agentick-be-api alembic upgrade head`

### Standard Response Format
```json
{
  "success": true,
  "message": "Information message",
  "data": { ... }
}
```

### 🧹 Code Quality (Ruff) - MANDATORY BEFORE PUSH

We use **Ruff** for lightning-fast linting, formatting, and automatic error fixing.
> [!IMPORTANT]
> To maintain high code quality and consistency, you **MUST** run the check, fix, and formatting commands before pushing any code to GitHub:
>
> 1. **Check & Auto-Fix Errors:**
>    ```bash
>    uv run ruff check . --fix
>    ```
> 2. **Format Code:**
>    ```bash
>    uv run ruff format .
>    ```

---

## 📚 Recommended Documentation

### 🏠 Internal Reference Guides
* **[docs/agent_guide.md](docs/agent_guide.md)** - Master configuration guide for AI Agent, OpenRouter, Opik Observability, and **Anthropic's "Building Effective Agents" Best Practices** applied.
* **[docs/models.md](docs/models.md)** - ERD and detailed SQLAlchemy database models.

### 🌐 Technology Ecosystem Docs
| Technology | Link |
| :--- | :--- |
| **FastAPI** | [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/) |
| **SQLAlchemy** | [https://www.sqlalchemy.org/](https://www.sqlalchemy.org/) |
| **Pydantic** | [https://docs.pydantic.dev/](https://docs.pydantic.dev/) |
| **Alembic** | [https://alembic.sqlalchemy.org/](https://alembic.sqlalchemy.org/) |
| **UV (Package Manager)** | [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/) |
| **PostgreSQL** | [https://www.postgresql.org/](https://www.postgresql.org/) |
| **Qdrant** | [https://qdrant.tech/](https://qdrant.tech/) |
| **Docker** | [https://www.docker.com/](https://www.docker.com/) |

