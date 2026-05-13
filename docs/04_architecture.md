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
- **Phân nhóm:** Mẫu Kiến trúc (Architectural Pattern) - Nhóm mở rộng cho Tầng Dữ liệu (Data Access Layer). Mẫu này nằm ở cấp độ bao quát (High-level) hơn các mẫu GoF để định hình cấu trúc của cả hệ thống Clean Architecture.
- **Định nghĩa:** Tách biệt triệt để logic truy cập dữ liệu (Data Access) khỏi logic nghiệp vụ (Business Logic). Tầng Repository đóng vai trò như một bộ sưu tập (collection) trong bộ nhớ, che giấu hoàn toàn việc truy vấn SQL hay tương tác ORM.
- **Ứng dụng & Lợi ích:** 
    - Che giấu độ phức tạp của SQLAlchemy ORM. Các Service hoàn toàn không biết về cấu trúc truy vấn CSDL, chỉ gọi các hàm chuẩn hóa (`find`, `create`, `update`).
    - Cho phép hoán đổi, nâng cấp thư viện ORM hoặc đổi hệ thống CSDL sau này mà không cần thay đổi một dòng code logic nghiệp vụ nào.
    - Hỗ trợ Unit Testing cực kỳ dễ dàng bằng cách mock tầng Repository.

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
- **Phân nhóm:** Structural Pattern (Nhóm Cấu trúc). Tương tự như Adapter hay Proxy, nó chịu trách nhiệm thiết lập, định nghĩa quan hệ phụ thuộc giữa các đối tượng/class mà không làm chúng dính chặt vào nhau.
- **Định nghĩa:** Thay vì một Class hay Function tự khởi tạo (new object) các đối tượng mà nó phụ thuộc vào, các phụ thuộc này sẽ được "bơm/tiêm" (inject) từ bên ngoài vào tại thời điểm thực thi bởi Framework.
- **Ứng dụng & Lợi ích:** 
    - Tận dụng cơ chế `Depends()` của FastAPI để tự động quản lý vòng đời (Lifecycle) của các thành phần như Database Session, Auth Token.
    - Giảm tính gắn kết chặt (Decoupling): Service layer không cần biết làm thế nào để tạo Database connection, chỉ cần khai báo "tôi cần DB" và Framework sẽ cung cấp.
    - Tự động dọn dẹp tài nguyên: Sử dụng Generator (`yield`) để đảm bảo session CSDL luôn được giải phóng (release connection pool) tự động sau khi request HTTP kết thúc.

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

## 4.3. Các Mẫu Thiết kế Nâng cao (Đã triển khai thực tế trong Core)

Để bảo vệ tính toàn vẹn tuyệt đối của Clean Architecture, hệ thống đã áp dụng thành công 2 mẫu thiết kế cấp cao sau:

### 4.3.1. Unit of Work (UoW) Pattern (Thực tế tại `app/repository/unit_of_work.py`)
- **Phân nhóm:** Behavioral Pattern (Nhóm Hành vi) mở rộng cho Giao dịch. Nó tương tự như Mẫu Command kết hợp Memento để theo dõi trạng thái thay đổi của một tập hợp đối tượng trước khi quyết định 'chốt' (commit) hành vi ghi dữ liệu.
- **Định nghĩa:** Theo dõi tất cả các thay đổi đối với các đối tượng/bảng dữ liệu trong một Transaction (giao dịch) duy nhất của nghiệp vụ, và đảm bảo đồng bộ hóa tất cả các thay đổi đó vào CSDL dưới dạng một "đơn vị công việc" duy nhất.
- **Ứng dụng & Lợi ích:** 
    - Đảm bảo tính nguyên tử tuyệt đối (Atomicity): Một nghiệp vụ phức tạp cần ghi vào 5 bảng khác nhau (ví dụ: Tạo User -> Tạo Team -> Cài Default Projects -> Gán Role) sẽ được gom lại. Nếu bước thứ 4 lỗi, hệ thống tự động `rollback` toàn bộ dữ liệu về trạng thái cũ, không sinh ra dữ liệu rác mồ côi.
    - Giải quyết bài toán truyền Session qua nhiều Repository, giúp giữ cho mã nguồn rõ ràng mà vẫn duy trì tính Atomic.

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
- **Phân nhóm:** Behavioral Pattern (Nhóm Hành vi) - Nằm trong 23 mẫu GoF kinh điển.
- **Định nghĩa:** Cho phép định nghĩa một gia đình các thuật toán/cách thức triển khai, đóng gói từng cái và khiến chúng có thể hoán đổi cho nhau tại thời điểm thực thi (Runtime).
- **Ứng dụng & Lợi ích:** 
    - Cô lập hoàn toàn "Logic bộ não AI" khỏi đặc thù kết nối của các nhà cung cấp dịch vụ LLM (OpenRouter, Gemini, Anthropic, OpenAI).
    - Hệ thống có khả năng chuyển đổi sang nhà cung cấp trí tuệ nhân tạo khác chỉ trong vòng 1 nốt nhạc thông qua việc đổi Class cài đặt (Strategy), miễn nhiễm hoàn toàn với việc đổi SDK bên thứ 3.

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
- **Phân nhóm:** Behavioral Pattern (Nhóm Hành vi) mở rộng (Concurrency). Định nghĩa hành vi thực thi, tương tác và phân phối tải giữa các luồng (Thread/Coroutine) làm việc đồng thời.
- **Định nghĩa:** Cơ chế điều phối và thực thi song song nhiều tác vụ bất đồng bộ (I/O Bound) một cách đồng thời, kết hợp với bộ giới hạn hạn ngạch (Throttling/Semaphores) để kiểm soát tài nguyên hệ thống.
- **Ứng dụng & Lợi ích:** 
    - Thay thế vòng lặp tuần tự bị nghẽn (Serial Bottleneck) bằng cơ chế Gom nhóm chạy song song sử dụng `asyncio.gather`.
    - Tận dụng `asyncio.Semaphore(N)` nhằm khống chế tốc độ gửi API tối đa, tránh bị dính giới hạn `429 Too Many Requests` từ OpenAI/OpenRouter mà vẫn đảm bảo thông lượng xử lý phân tích hàng trăm task cùng lúc tăng gấp 500%.

### 4.4.2. Infallible Fallback Parser Pattern (Thực tế tại `app/services/risk_analysis_service.py`)
- **Phân nhóm:** Behavioral Pattern (Nhóm Hành vi) - Áp dụng mẫu **Chain of Responsibility (Chuỗi trách nhiệm)** của GoF. Các Parser được sắp xếp thành một chuỗi; nếu thằng trước giải quyết thất bại, yêu cầu được chuyển cho thằng đứng sau giải cứu.
- **Định nghĩa:** Chuỗi các cơ chế giải mã và phục hồi dữ liệu xếp tầng (Multi-layered recovery). Khi một cơ chế parse dữ liệu thất bại, cơ chế tiếp theo với mức độ bao dung (tolerance) cao hơn sẽ được kích hoạt để cố gắng cứu vãn thông tin.
- **Ứng dụng & Lợi ích:** 
    - Khắc phục triệt để điểm yếu "ảo giác" định dạng JSON của các dòng LLM nhỏ. Đảm bảo Server luôn cứu vãn được kết quả thay vì bị crash 500 Error.
    - **Tầng 1**: Chạy `json.loads()` tiêu chuẩn.
    - **Tầng 2**: Chạy Cleanse Parser (Fix các dấu ngoặc bị thiếu, xóa ký tự lạ Markdown code block).
    - **Tầng 3**: Dùng Regex Scrapers (Cố gắng cào bóc tách riêng số điểm rủi ro từ một đoạn text hỗn loạn của AI).
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
