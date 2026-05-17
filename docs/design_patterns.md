# Các Design Pattern Áp Dụng Trong Agentick-BE

Ngoài Clean Architecture, dự án còn ứng dụng sâu sắc các Design Pattern để giải quyết những bài toán đặc thù. Dưới đây là phân tích chi tiết về 4 pattern trọng tâm được sử dụng trong codebase.

---

## 1. Repository Pattern + Service Layer

### 1.1. Định nghĩa
- **Repository Pattern:** Đóng vai trò là một lớp trung gian giữa ứng dụng và cơ sở dữ liệu. Nó che giấu đi sự phức tạp của các câu truy vấn ORM (SQLAlchemy) và cung cấp các hàm API thao tác với dữ liệu như thao tác với Collection trong bộ nhớ.
- **Service Layer:** Đóng gói toàn bộ logic nghiệp vụ (business logic) của ứng dụng, đứng giữa giao diện giao tiếp (Controller) và lớp dữ liệu (Repository).

### 1.2. Thuộc nhóm
- Nhóm **Architectural Patterns** (mẫu kiến trúc), nổi tiếng từ triết lý **Domain-Driven Design (DDD)** của Eric Evans.

### 1.3. So sánh với truyền thống (Java/Spring MVC)
- Ở Spring/Java, bạn thường thấy `Controller ➔ @Service ➔ @Repository (DAO)`. Ở Java, Repository thường phải định nghĩa rõ các `Interface` (VD: `ITaskRepository`) và `Class Impl`.
- Ở **FastAPI (Python)**, do tính chất "duck-typing" của Python, dự án thường không bắt buộc phải tạo file Interface riêng biệt mà sử dụng các base class (`BaseRepository`, `BaseService`) dùng chung qua kế thừa (Inheritance).

### 1.4. Bài toán giải quyết
- Giúp Controller (API Endpoint) trở nên siêu mỏng (Thin Controller). Controller không biết dữ liệu được lưu bằng Postgres hay MongoDB.
- Tái sử dụng logic nghiệp vụ ở nhiều nơi (vd: HTTP API, Background Worker, CLI).
- Dễ dàng viết Unit Test bằng cách mock Repository thay vì phải kết nối thẳng tới Database thật.

### 1.5. Code thực tế trong dự án
- **Repository:**
```python
# app/repository/task_repository.py
from app.repository.base_repository import BaseRepository
from app.model.task import Task

class TaskRepository(BaseRepository):
    def __init__(self, session_factory):
        super().__init__(session_factory, Task)

    # Đóng gói logic query bằng SQLAlchemy
    def get_active_task_ids_by_project(self, project_id: str) -> list[str]:
        with self.session_factory() as session:
            tasks = session.query(self.model).filter(
                self.model.project_id == project_id,
                self.model.is_deleted.is_(False)
            ).all()
            return [t.id for t in tasks]
```

- **Service:**
```python
# app/services/task_service.py
from app.services.base_service import BaseService

class TaskService(BaseService):
    def __init__(self, repository, project_member_repo=None):
        super().__init__(repository)
        self.project_member_repo = project_member_repo

    # Xử lý Business Logic
    def get_my_tasks(self, user_id: str, team_id: str | None = None):
        user_member_ids = self.project_member_repo.get_member_ids_by_user(user_id)
        if not user_member_ids:
            return []
        # Gọi xuống Repository
        return self._repository.get_my_tasks_complex(user_id, user_member_ids, team_id)
```

---

## 2. Dependency Injection (DI)

### 2.1. Định nghĩa
Là kỹ thuật mà một object không tự tạo ra các "phụ thuộc" (dependency) của nó (ví dụ như DB Session, Service instance), mà sẽ được cung cấp (inject) từ bên ngoài truyền vào.

### 2.2. Thuộc nhóm
- Nhóm **Creational Patterns** (Nguyên lý Inversion of Control - IoC).

### 2.3. So sánh với truyền thống (Java/Spring MVC)
- Trong Java Spring, DI thường được cấu hình tập trung ở Container (IoC Container) và inject thông qua các annotation như `@Autowired` quét lúc khởi động (startup).
- Trong **FastAPI**, DI là một công dân hạng nhất (First-class citizen) được nhúng thẳng vào hệ thống routing qua hàm `Depends()`. Việc tiêm phụ thuộc được tính toán linh hoạt theo từng request (Request-scoped), thay vì inject toàn cầu.

### 2.4. Bài toán giải quyết
- Tránh việc khởi tạo cứng (Hard-code instantiation) như `service = TaskService()` ngay trong endpoint, giúp code lỏng lẻo hơn (loose coupling).
- Dễ dàng thay thế dependency thật bằng phiên bản "Mock" khi chạy pytest (overriding dependencies).

### 2.5. Code thực tế trong dự án
```python
# app/api/v1/endpoints/tasks.py
from fastapi import Depends
from app.core.dependencies import get_db

# 1. Hàm khởi tạo và kết nối các phụ thuộc
def get_task_service(db=Depends(get_db)) -> TaskService:
    # DB session được inject vào Repository, Repository lại được inject vào Service
    task_repository = TaskRepository(lambda: nullcontext(db))
    return TaskService(repository=task_repository)

# 2. Endpoints sử dụng DI
@router.post("")
def create_task(
    schema: TaskCreate,
    # Inject Service tự động dựa trên Depends
    service: TaskService = Depends(get_task_service)
):
    result = service.add(schema)
    return ResponseSchema(data=result)
```

---

## 3. Unit of Work (UoW)

### 3.1. Định nghĩa
Unit of Work duy trì một danh sách các đối tượng bị ảnh hưởng bởi một giao dịch nghiệp vụ (business transaction) và đảm bảo tất cả các thay đổi sẽ được "commit" một lần duy nhất, hoặc "rollback" tất cả nếu có lỗi.

### 3.2. Thuộc nhóm
- Nhóm **Architectural Patterns / Concurrency Pattern** (Martin Fowler).

### 3.3. So sánh với truyền thống (Java/Spring MVC)
- Ở Spring, bạn chỉ cần đánh dấu `@Transactional` trên phương thức Service, framework sẽ dùng AOP (Aspect-Oriented Programming) để tự động quản lý transaction ẩn dưới nền.
- Ở **Python/FastAPI**, chúng ta thường phải tự triển khai pattern này rõ ràng (Explicit) thông qua **Context Manager** (`with ... as ...:`) của Python.

### 3.4. Bài toán giải quyết
- Khi một nghiệp vụ phải ghi dữ liệu vào nhiều bảng (vd: Tạo Project -> Tạo Project Member -> Tạo Cấu hình TaskStatus). Nếu cập nhật bảng 1 thành công nhưng bảng 2 thất bại, dữ liệu sẽ bị "rác". UoW đảm bảo tính chất **ACID** (Atomic), ghi thành công thì lưu tất cả, lỗi thì hoàn tác (rollback) toàn bộ.
- Chia sẻ **cùng một DB session** cho nhiều Repository khác nhau.

### 3.5. Code thực tế trong dự án
```python
# app/repository/unit_of_work.py
from contextlib import nullcontext

class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def __enter__(self):
        # Mở một transaction duy nhất
        self._cm = self.session_factory()
        self.session = self._cm.__enter__()

        def active_session_factory():
            return nullcontext(self.session)

        # Inject cùng 1 session cho TẤT CẢ repositories
        self.projects = ProjectRepository(active_session_factory)
        self.project_members = ProjectMemberRepository(active_session_factory)
        self.task_statuses = TaskStatusRepository(active_session_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.session.rollback() # Hoàn tác nếu có exception
            else:
                self.session.commit() # Lưu tất cả nếu thành công
        finally:
            self._cm.__exit__(exc_type, exc_val, exc_tb)

# Cách sử dụng trong Service
# with UnitOfWork(session_factory) as uow:
#     uow.projects.create(...)
#     uow.project_members.create(...)
```

---

## 4. Strategy Pattern

### 4.1. Định nghĩa
Định nghĩa một họ các thuật toán/hành vi, đóng gói từng thuật toán lại vào một class riêng, và làm cho chúng có thể hoán đổi cho nhau tại thời điểm chạy (runtime) mà không làm ảnh hưởng đến client đang sử dụng nó.

### 4.2. Thuộc nhóm
- Nhóm **Behavioral Patterns** (Mẫu hành vi của GoF - Gang of Four).

### 4.3. So sánh với truyền thống (Java/Spring MVC)
- Rất giống với cách Java triển khai: Tạo một `Interface` chung và nhiều class `Implements` interface đó. Hệ thống sẽ chọn implementation phù hợp thông qua Factory hoặc DI.
- Trong **Python**, chúng ta sử dụng `abc.ABC` và decorator `@abstractmethod` để giả lập Interface thay vì có từ khóa `interface` riêng như Java.

### 4.4. Bài toán giải quyết
- Trong Agentick, chúng ta giao tiếp với các LLM Models (AI) khác nhau. Thay vì viết những câu `if/else` chằng chịt trong code (VD: `if model == "gemini": ... elif model == "openai": ...`), ta tạo ra các "Chiến lược" (Strategy) khác nhau cho từng nhà cung cấp.
- Giúp tuân thủ nguyên lý **Open/Closed Principle**: Dễ dàng thêm provider mới (như Claude) mà không cần sửa code cũ.

### 4.5. Code thực tế trong dự án
```python
# app/agents/llm_strategy.py
from abc import ABC, abstractmethod

# 1. Interface (Strategy)
class LLMStrategy(ABC):
    @abstractmethod
    async def generate_chat_completion(self, messages, tools=None, tool_choice="auto", response_format=None):
        pass

# 2. Concrete Strategy 1: Gọi qua OpenRouter
class OpenRouterStrategy(LLMStrategy):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    async def generate_chat_completion(self, messages, tools=None, ...):
        # Triển khai HTTP call tới OpenRouter
        async with httpx.AsyncClient() as client:
            response = await client.post(...)
            return response.json()

# 3. Concrete Strategy 2: Gọi trực tiếp Gemini
class GeminiDirectStrategy(LLMStrategy):
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    async def generate_chat_completion(self, messages, tools=None, ...):
        # Triển khai logic gọi Gemini SDK trực tiếp
        raise NotImplementedError("GeminiDirectStrategy is ready for integration.")

# Khi dùng (Context), chúng ta chỉ gọi:
# strategy = OpenRouterStrategy(...)
# response = await strategy.generate_chat_completion(...)
```
