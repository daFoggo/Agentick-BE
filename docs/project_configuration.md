# Cấu hình Dự án & Lớp Core (app/core)

Dự án Agentick-BE quản lý các thiết lập môi trường và luồng xử lý cốt lõi một cách tập trung, giúp tách biệt hoàn toàn giữa cấu hình hạ tầng và logic nghiệp vụ.

---

## 1. Cấu hình Docker & Triển khai

### 1.1. Dockerfile
Dự án sử dụng hình ảnh Docker được tối ưu hóa cực cao nhờ kết hợp **uv** (trình quản lý package siêu tốc bằng Rust) và **multi-stage build**.

- **Chức năng:** Xây dựng môi trường chạy ứng dụng. Nó sử dụng cơ chế cache hiệu quả của `uv` để cài đặt dependencies từ `uv.lock` và `pyproject.toml` trước khi copy mã nguồn, giúp tăng tốc quá trình build docker image.
- **Code thực tế:**
```dockerfile
# Sử dụng uv để quản lý package siêu nhanh
FROM ghcr.io/astral-sh/uv:latest AS uv_bin
FROM python:3.12-slim

COPY --from=uv_bin /uv /uvx /bin/
WORKDIR /app

# Cài đặt dependencies với cache
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### 1.2. docker-compose.yml
- **Chức năng:** Quản lý môi trường triển khai cục bộ (Local Development) và hạ tầng. Khởi tạo đồng loạt 3 container:
  - `api`: Chạy backend FastAPI, gắn với file biến môi trường (`.env`, `.env.dev`).
  - `db`: PostgreSQL phiên bản 18, lưu trữ dữ liệu chính.
  - `qdrant`: Vector Database phục vụ cho Vector Search & RAG.
- **Code thực tế:**
```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
  db:
    image: postgres:18
    ports:
      - "5433:5432"
    volumes:
      - agentick_be_data:/var/lib/postgresql
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
```

---

## 2. Cấu trúc Lớp Core (`app/core/`)

Thư mục `app/core/` chứa toàn bộ trái tim của hệ thống: Cấu hình, kết nối DB, bảo mật, và lập lịch.

### 2.1. `config.py` (Quản lý Biến Môi trường)
- **Chức năng:** Sử dụng `pydantic-settings` để load và xác thực tự động các biến môi trường từ file `.env` hoặc hệ điều hành. Báo lỗi ngay lập tức khi start server nếu thiếu các biến bắt buộc (VD: Thiếu URL kết nối DB).
- **Code thực tế:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "agentick-be"
    ENV: Environment = Environment.DEV
    
    # Auth & JWT
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DATABASE_URL: str | None = None

    # LLM & Third-parties
    OPENROUTER_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=[".env", ".env.dev"],
        extra="ignore"
    )

settings = Settings()
```

### 2.2. `dependencies.py` (Dependency Injection Cốt lõi)
- **Chức năng:** Cung cấp các hàm "Tiêm Phụ Thuộc" dùng chung cho toàn bộ Endpoints của hệ thống. Quan trọng nhất là việc cấp phát phiên giao dịch DB (`get_db`) và xác thực người dùng (`get_current_active_user`).
- **Code thực tế:**
```python
from fastapi import Depends
from app.core.database import Database
from app.model.user import User

# Generator quản lý vòng đời của Database Session cho mỗi Request
def get_db() -> Generator:
    with get_database().session() as session:
        yield session

# Phân tích JWT Token và truy vấn Database để xác thực
def get_current_user(payload: dict = Depends(get_token_payload), db=Depends(get_db)) -> User:
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthError(detail="User not found.")
    return user
```

### 2.3. `scheduler.py` (Lập lịch Tác vụ Ngầm)
- **Chức năng:** Hệ thống dùng `APScheduler` để điều phối các tác vụ chạy ngầm độc lập với HTTP Request. Nó tuân thủ chặt chẽ Architecture bằng cách gọi trực tiếp xuống Database hoặc các Service nghiệp vụ.
- **Ví dụ tác vụ:**
  - `morning_scan_job`: Chạy lúc 9h sáng mỗi ngày, quét toàn bộ tasks chưa hoàn thành và gọi `RiskAnalysisService` (LLM Agent) để phân tích rủi ro dự án.
  - `evening_summary_job`: Tổng hợp các Risk Snapshot và tự động gửi Email báo cáo lúc chiều.
- **Code thực tế:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler(timezone=timezone("UTC"))

async def morning_scan_job():
    # ... logic tìm kiếm tasks cần scan
    await local_analyzer.analyze_task(t_obj.id)

def start_scheduler():
    # Quét rủi ro vào mỗi đầu giờ sáng
    scheduler.add_job(morning_scan_job, "cron", minute=0, id="morning_scan")
    # Gửi báo cáo chiều
    scheduler.add_job(evening_summary_job, "cron", minute=30, id="evening_summary")
    scheduler.start()
```

### 2.4. `security.py` & `exceptions.py`
- **`security.py`:** Chứa hàm băm mật khẩu (Bcrypt/Passlib), khởi tạo mã thông báo chuẩn JWT (encode/decode) đảm bảo tính toàn vẹn của Identity.
- **`exceptions.py`:** Trọng tâm xử lý lỗi tập trung. Định nghĩa các base exception như `AuthError`, `NotFoundError`. Việc ném exception (throw error) ở Service hay Repository sẽ được FastAPI bắt lại thông qua Exception Handler và biến thành các mã HTTP Error Code (400, 401, 404) chuẩn hóa.
