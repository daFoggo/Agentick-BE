# Clean Architecture trong Agentick-BE

Dự án tuân theo chuẩn **Clean Architecture** kết hợp với **Modular Monolith**. Nguyên tắc cốt lõi của kiến trúc này là **Quy tắc phụ thuộc (Dependency Rule)**: Các thành phần bên ngoài (Framework, DB, UI) phụ thuộc vào các thành phần bên trong (Use Cases, Entities), và không có chiều ngược lại.

**Quy tắc điều hướng (Dependency Direction) trong dự án:**  
`Endpoint` (Controller) ➔ `Service` (Use Case) ➔ `Repository` (Gateway) ➔ `Model & Schema` (Entities).

## 1. Ảnh minh họa Clean Architecture

![Clean Architecture](https://blog.cleancoder.com/uncle-bob/images/2012-08-13-the-clean-architecture/CleanArchitecture.jpg)

## 2. Phân tích chức năng "Tạo Task" qua từng Domain

### A. Entities (Thực thể & Cấu trúc Dữ liệu - Core Business Rules)
**Vị trí thư mục:** `app/model/` và `app/schema/`
- **Nhiệm vụ:** Định nghĩa cấu trúc dữ liệu cốt lõi, ánh xạ bảng CSDL và quy tắc kiểm tra tính hợp lệ của Request/Response. Không chứa logic HTTP hay điều hướng.

**Hình ảnh Code (Model):**
```python
# app/model/task.py (Lược trích)
from app.model.base_model import BaseModel
from sqlalchemy import Column, String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

class Task(BaseModel):
    __tablename__ = "task"

    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("project.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status_id: Mapped[str] = mapped_column(String(36), ForeignKey("task_status.id"), nullable=False)
    
    # Relationships
    project: Mapped["Project"] = relationship("Project")
    task_members: Mapped[list["TaskMember"]] = relationship("TaskMember", back_populates="task")
```

**Hình ảnh Code (Schema):**
```python
# app/schema/task_schema.py (Lược trích)
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TaskCreate(BaseModel):
    project_id: str
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status_id: str
    type_id: str
    priority_id: str
    member_ids: Optional[List[str]] = None
    due_date: datetime
```

### B. Use Cases (Quy tắc Nghiệp vụ Ứng dụng - Services)
**Vị trí thư mục:** `app/services/`
- **Nhiệm vụ:** Chứa toàn bộ logic nghiệp vụ (Business Orchestration). Service nhận dữ liệu từ Controller, áp dụng quy tắc kinh doanh, gọi xuống Repository và điều phối các tác vụ phụ.

**Hình ảnh Code (Service):**
```python
# app/services/task_service.py (Lược trích)
from typing import Any
from app.services.base_service import BaseService

class TaskService(BaseService):
    def add(self, schema: Any, acting_user_id: str = None) -> Any:
        # 1. Gọi Repository để thực hiện lưu trữ Task mới vào DB
        result = self._repository.create(schema, acting_user_id=acting_user_id)
        
        # 2. Logic Nghiệp vụ: Điều phối tạo thông báo Notification cho các members
        if hasattr(schema, "member_ids") and schema.member_ids:
            self._repository.create_task_assignment_notifications(
                result.id, schema.member_ids
            )
            
        # 3. Trả về Task hoàn chỉnh (kèm theo các relation)
        return self.get_by_id(result.id)
```

### C. Interface Adapters (Bộ chuyển đổi - Repositories & Endpoints)

**1. Repositories (Gateways - Xử lý Database Query)**  
**Vị trí thư mục:** `app/repository/`
- **Nhiệm vụ:** Thực thi chi tiết truy vấn DB bằng SQLAlchemy. Là cầu nối giữa Service và CSDL. Tuyệt đối không chứa logic kinh doanh.

**Hình ảnh Code (Repository):**
```python
# app/repository/task_repository.py (Lược trích)
from app.repository.base_repository import BaseRepository
from app.model.task_member import TaskMember

class TaskRepository(BaseRepository):
    def create(self, schema, acting_user_id: str = None, auto_commit=True):
        data = schema.model_dump()
        member_ids = data.pop("member_ids", []) or []

        with self.session_factory() as session:
            # 1. Khởi tạo Model
            item = self.model(**data)
            session.add(item)
            session.flush() # Lấy ID tạm thời trước khi commit

            # 2. Thêm người tạo làm 'Lead'
            if acting_user_id:
                session.add(TaskMember(task_id=item.id, user_id=acting_user_id, role="lead"))

            # 3. Thêm các members khác
            for uid in member_ids:
                if uid != acting_user_id:
                    session.add(TaskMember(task_id=item.id, user_id=uid, role="member"))

            if auto_commit:
                session.commit()
                # 4. Trigger đồng bộ lưu Vector Search lên Qdrant chạy ngầm
                from app.utils.qdrant_helper import upsert_task_vector, run_async_background
                run_async_background(upsert_task_vector(item.id, item.title, item.description, item.project_id))
                
            return item
```

**2. Endpoints (Controllers - Xử lý HTTP Request/Response)**  
**Vị trí thư mục:** `app/api/v1/endpoints/`
- **Nhiệm vụ:** Nhận HTTP Request, tiêm phụ thuộc (Dependency Injection), truyền thông tin tới Service và đóng gói chuẩn hóa đầu ra qua `ResponseSchema`.

**Hình ảnh Code (Endpoints):**
```python
# app/api/v1/endpoints/tasks.py (Lược trích)
from contextlib import nullcontext
from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_active_user, get_db
from app.schema.base_schema import ResponseSchema
from app.schema.task_schema import TaskCreate, TaskRead
from app.services.task_service import TaskService
from app.repository.task_repository import TaskRepository
from app.model.user import User

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Dependency Injection cho phép cung cấp DB Session cho Repository và truyền vào Service
def get_task_service(db=Depends(get_db)) -> TaskService:
    task_repository = TaskRepository(lambda: nullcontext(db))
    return TaskService(repository=task_repository)

@router.post("", response_model=ResponseSchema[TaskRead])
def create_task(
    schema: TaskCreate,  # Parse & Validate tự động bằng Pydantic Schema
    current_user: User = Depends(get_current_active_user), # Xác thực User
    service: TaskService = Depends(get_task_service), # Inject Service
):
    # Chỉ truyền thông tin xuống Service
    result = service.add(schema, acting_user_id=current_user.id)
    
    # Đóng gói Response trả về Frontend
    return ResponseSchema(data=result, message="Task created successfully")
```

### D. Frameworks & Drivers (Lớp ngoài cùng)
**Vị trí:** `app/main.py`, `app/core/`, `app/db/`
- **Nhiệm vụ:** Đăng ký app FastAPI, đăng ký Middlewares, cấu hình Database (PostgreSQL), thiết lập Scheduler và kết nối tới external services.

## 3. Tổng kết luồng dữ liệu (Data Flow) khi tạo Task
1. Frontend gửi `POST /api/v1/tasks`.
2. **Framework (FastAPI)** chuyển request tới Controller (`tasks.py`).
3. **Controller** dùng **Schema (`TaskCreate`)** kiểm tra đầu vào, dùng Auth xác thực User, và gọi **Service (`TaskService`)**.
4. **Service** điều phối luồng, gọi **Repository (`TaskRepository`)**.
5. **Repository** dùng **Model (`Task`)** thao tác với SQL DB, lưu dữ liệu, đẩy dữ liệu sang Qdrant và trả Model thể hiện ra.
6. **Service** thấy có assign members thì tiếp tục gọi Repository để lưu thông báo (Notification). Xong xuôi trả kết quả lại.
7. **Controller** bọc kết quả vào **Schema (`ResponseSchema`)** và trả JSON sạch sẽ về cho Frontend.
