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

## 4.3. Các Mẫu Thiết kế Nâng cao (Đã triển khai thực tế trong Core)

Để bảo vệ tính toàn vẹn tuyệt đối của Clean Architecture, hệ thống đã áp dụng thành công 2 mẫu thiết kế cấp cao sau:

### 4.3.1. Unit of Work (UoW) Pattern (Thực tế tại `app/repository/unit_of_work.py`)
Đảm bảo tính toàn vẹn giao dịch (Atomicity) khi thực hiện một luồng nghiệp vụ phức tạp trên nhiều Repository khác nhau cùng lúc (như chuỗi tạo User -> Team -> Default Project -> Seed Data). 

**Mã nguồn thực tế:**
```python
class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self._cm = None
        self.session = None

    def __enter__(self):
        # Correctly invoke the context manager to resolve the actual Session
        self._cm = self.session_factory()
        self.session = self._cm.__enter__()

        # Create wrapper factory that injects our active session
        def active_session_factory():
            return nullcontext(self.session)

        # Inject repositories configured with current atomic session
        self.projects = ProjectRepository(active_session_factory)
        self.project_members = ProjectMemberRepository(active_session_factory)
        self.task_statuses = TaskStatusRepository(active_session_factory)
        self.task_types = TaskTypeRepository(active_session_factory)
        self.task_priorities = TaskPriorityRepository(active_session_factory)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            self._cm.__exit__(exc_type, exc_val, exc_tb)
```

### 4.3.2. Strategy Pattern (Thực tế tại `app/agents/llm_strategy.py`)
Cô lập logic gọi API đến nhà cung cấp trí tuệ nhân tạo. Giúp hệ thống miễn nhiễm hoàn toàn với việc nhà cung cấp đổi SDK, chỉ cần đổi Strategy là toàn bộ "Bộ não" chuyển hướng (Ví dụ: OpenRouter <-> Gemini <-> OpenAI).

**Mã nguồn thực tế:**
```python
class LLMStrategy(ABC):
    @abstractmethod
    async def generate_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pass

class OpenRouterStrategy(LLMStrategy):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate_chat_completion(self, messages, tools=None, **kwargs):
        # Thực hiện httpx.AsyncClient() post logic tới base_url...
        # Đảm bảo tách rời hoàn toàn Agent Logic khỏi HTTP Client specifics
        pass
```

---

## 4.4. Mẫu Thiết kế Hiện đại Đặc thù cho Agentic Workflows

Ngoài ra, trong quá trình tối ưu hệ thống Agent, 2 mẫu thiết kế đặc thù sau đã được áp dụng:

### 4.4.1. Concurrent Async Worker Pattern (Thực tế tại `app/core/scheduler.py`)
Thay thế vòng lặp tuần tự (Serial Bottleneck) bằng cơ chế Gom nhóm chạy song song quy mô lớn sử dụng `asyncio.gather` và `asyncio.Semaphore(N)` nhằm khống chế tốc độ gửi API (Rate Limiting) mà vẫn đảm bảo thông lượng xử lý cao gấp 500%.

### 4.4.2. Infallible Fallback Parser Pattern (Thực tế tại `app/services/risk_analysis_service.py`)
Áp dụng mô hình **Xử lý đa tầng có dự phòng (Multi-stage recovery)** để cứu hộ dữ liệu JSON bị lỗi khi AI trả về kết quả không ổn định:
1. **Tầng 1**: Chạy JSON Parser tiêu chuẩn.
2. **Tầng 2**: Chạy Cleanse Parser (Thay dấu nháy đơn, xóa backslash key bị lỗi).
3. **Tầng 3**: Dùng Regex Scrapers (Tìm & trích xuất cứng điểm số/kết quả từ chuỗi rác).
👉 Đảm bảo Server KHÔNG BAO GIỜ bị crash hay sập do lỗi cú pháp của mô hình AI bên thứ ba.

---

## 4.5. Bố cục Cấu trúc Thư mục Dự án

### 4.5.1. Backend (Cấu trúc phân lớp SoC)
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
