# 4. Kiến trúc Phần mềm & Mẫu thiết kế (Architecture & Design Patterns)

Tài liệu này đặc tả chi tiết kiến trúc tổng thể và các Mẫu thiết kế (Design Patterns) thực tế đang vận hành trong mã nguồn của dự án Agentick. Hệ thống tuân thủ nghiêm ngặt triết lý **Clean Architecture** và mô hình **Modular Monolith** hiện đại.

---

## 4.1. Kiến trúc Tổng thể: Modular Monolith

Agentick-BE được xây dựng theo mô hình **Kiến trúc Nguyên khối dạng Mô-đun (Modular Monolith)**. 

- **Đặc trưng**: Toàn bộ hệ thống chạy chung một ứng dụng nhưng mã nguồn được chia cắt rất rõ ràng theo chức năng độc lập thông qua cấu trúc cây thư mục tách biệt (`app/repository`, `app/services`, `app/agents`).
- **Lợi ích**: Đảm bảo tính nhất quán (Data Consistency) cực cao trong cùng 1 CSDL PostgreSQL, nhưng đã được Module hóa sẵn sàng 100% để bóc tách sang Microservices (ví dụ: chuyển Agent Core sang một Server riêng) khi hệ thống scale-up.

---

## 4.2. Các Design Patterns Thực tế trong Codebase (Thực dụng & Áp dụng thật)

### 4.2.1. Repository Pattern & Service Layer (Thực tế tại `app/repository/base_repository.py`)
Dự án đã xây dựng thành công lớp abstraction **BaseRepository** che giấu triệt để độ phức tạp của SQLAlchemy. Các Service chỉ gọi qua hàm chuẩn để đảm bảo tính độc lập.

**Mã nguồn thực tế trích từ BaseRepository:**
```python
# app/repository/base_repository.py
class BaseRepository:
    def __init__(self, session_factory: Callable[..., AbstractContextManager[Session]], model: Type[T]) -> None:
        self.session_factory = session_factory
        self.model = model

    def create(self, schema: T | dict, auto_commit: bool = True):
        data = schema.model_dump() if hasattr(schema, "model_dump") else schema
        with self.session_factory() as session:
            query = self.model(**data)
            session.add(query)
            if auto_commit:
                session.commit()
                session.refresh(query)
            return query
```

### 4.2.2. Dependency Injection (DI) Pattern (Thực tế tại `app/core/dependencies.py`)
Sử dụng cơ chế `Depends()` tối thượng của FastAPI để chia sẻ tài nguyên (Database session) và tự động làm sạch dữ liệu sau khi kết thúc một Request.

**Mã nguồn thực tế trích từ dependencies:**
```python
# app/core/dependencies.py
def get_db() -> Generator:
    # Tự động mở Context Manager cấp Request
    with get_database().session() as session:
        yield session
    # Tự động đóng và release connection pool tại đây

def get_current_user(payload: dict[str, Any] = Depends(get_token_payload), db=Depends(get_db)) -> User:
    # Tự động tiêm DB và User Token vào Controller
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    return user
```

### 4.2.3. Lifespan Pattern (Thực tế tại `app/main.py`)
Kiểm soát tuyệt đối vòng đời bật/tắt của ứng dụng để quản trị Background Jobs (như Scheduler của AI Agent) giúp tài nguyên máy chủ không bị leak.

**Mã nguồn thực tế trích từ app/main.py:**
```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chạy khi khởi động Server: Bật scheduler ngầm
    start_scheduler()
    yield
    # Chạy khi tắt Server: Đảm bảo Scheduler đã dừng an toàn
    shutdown_scheduler()
```

---

## 4.3. Các Mẫu Thiết kế Nâng cao (Chiến lược Refactor Tương lai)

Để bảo vệ tính toàn vẹn tuyệt đối của Clean Architecture khi mở rộng quy mô lớn, dự án hoạch định áp dụng 2 mẫu thiết kế cấp cao sau:

### 4.3.1. Unit of Work (UoW) Pattern (Giao dịch Nguyên tử)
Phục vụ khi cần cập nhật đồng bộ nhiều bảng trong cùng một luồng business (ví dụ: Tạo Project, tự động Seed Status, Type, Priority). Đảm bảo "Được ăn cả, ngã về không".

**Ví dụ triển khai (Dự định):**
```python
class UnitOfWork:
    def __enter__(self):
        self.session = session_factory()
        # Tất cả Repo dùng chung DUY NHẤT 1 instance session
        self.projects = ProjectRepository(lambda: self.session)
        self.catalogs = CatalogRepository(lambda: self.session)
        return self
    
    def __exit__(self, exc_type, ...):
        if exc_type: self.session.rollback() # Hoàn tác toàn bộ nếu lỗi bất kì
        else: self.session.commit()          # Lưu lại tất cả cùng lúc
```

### 4.3.2. Strategy Pattern (Chiến lược chuyển đổi AI Agent)
Giúp tách rời Core Logic của Agent khỏi nhà cung cấp mô hình cụ thể (LLM Vendor), cho phép chuyển đổi giữa OpenRouter, Google Gemini hoặc OpenAI chỉ qua một biến Config cấu hình.

**Ví dụ cấu trúc mã nguồn (Dự định):**
```python
from abc import ABC, abstractmethod

class LLMStrategy(ABC):
    @abstractmethod
    async def ask(self, prompt: str) -> str: pass

class GeminiStrategy(LLMStrategy):
    async def ask(self, prompt): return await gemini_sdk.call(prompt)

class CustomAgent:
    def __init__(self, model_strategy: LLMStrategy):
        self.engine = model_strategy
    
    async def run(self, prompt):
        # Tuyệt đối không bị phụ thuộc vào thư viện của bên thứ 3 nào
        return await self.engine.ask(prompt) 
```

---

## 4.4. Bố cục Cấu trúc Thư mục Dự án

### 4.4.1. Backend (Cấu trúc phân lớp SoC)
```text
Agentick-BE/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/  # Route Handlers (Giao thức HTTP).
│   ├── model/          # Database Domain Entities.
│   ├── schema/         # Pydantic DTOs (Validation/Serialization).
│   ├── repository/     # Data Access Layer (Đã cài đặt BaseRepository).
│   ├── services/       # Business Core Logic (Tách biệt Router).
│   ├── agents/         # AI Logic, Prompts & Agentic Workflows.
│   └── main.py         # Cài đặt Lifespan & Setup application.
```

### 4.4.2. Frontend Feature-Driven Architecture
Nhóm mã nguồn theo từng "Tính năng lớn" của doanh nghiệp.
```text
Agentick-FE/
├── src/
│   ├── features/         # DOMAIN-BASED SLICES
│   │   ├── agent/        # Dashboard & Risk AI components
│   │   ├── projects/     # Board, List, Settings logic
│   │   ├── tasks/        # Task modals, editors
│   ├── routes/           # Cây thư mục Định tuyến File-based
```
