# Agentick Backend

Agentick is an AI Agent-powered project management platform that proactively detects deadline risks and improves deadline estimation over time using accumulated execution behavior data.

---

## 🚀 Installation & Setup

This project uses **Docker** and **Alembic** to ensure a consistent environment and database schema. 

### 1. Environment Configuration
Create a `.env` file in the root directory (where `docker-compose.yml` is located) with the following variables:
```env
# Database Credentials
POSTGRES_USER=agentick_user
POSTGRES_PASSWORD=agentick_password
POSTGRES_DB=agentick_db
DATABASE_URL=postgresql://agentick_user:agentick_password@db:5432/agentick_db

# Security
SECRET_KEY=your_super_secret_key
ENV=dev
```
> [!IMPORTANT]
> Never commit the `.env` file to version control.

### 2. Starting the System with Docker
We use Docker Compose to orchestrate the API and Database containers.
```bash
docker compose up -d --build
```
*Wait 5-10 seconds for the database to be ready.*

### 3. Database Migrations (Alembic)
The database starts empty. You must apply migrations to create the tables.
```bash
docker exec agentick-be-api alembic upgrade head
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
- `app/services/`: Contains core business logic and cross-repository coordination.
- `app/repository/`: Handles data access and SQLAlchemy queries (Inherits from `base_repository.py`).
- `app/model/`: Defines database tables using SQLAlchemy (Inherits from `base_model.py`).
- `app/schema/`: Defines data validation and serialization using Pydantic.
- `app/core/`: System-wide configurations (Security, Database, Dependencies).
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

---

## 📚 Recommended Documentation

| Technology | Link |
| :--- | :--- |
| **FastAPI** | [https://fastapi.tiangolo.com/](https://fastapi.tiangolo.com/) |
| **SQLAlchemy** | [https://www.sqlalchemy.org/](https://www.sqlalchemy.org/) |
| **Pydantic** | [https://docs.pydantic.dev/](https://docs.pydantic.dev/) |
| **Alembic** | [https://alembic.sqlalchemy.org/](https://alembic.sqlalchemy.org/) |
| **UV (Package Manager)** | [https://docs.astral.sh/uv/](https://docs.astral.sh/uv/) |
| **PostgreSQL** | [https://www.postgresql.org/](https://www.postgresql.org/) |
| **Docker** | [https://www.docker.com/](https://www.docker.com/) |
