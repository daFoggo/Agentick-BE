# 3. Sơ đồ Hệ thống UML (UML System Diagrams)

Tài liệu này cung cấp đầy đủ bộ bản vẽ chuẩn UML phục vụ trực tiếp cho công tác phân tích nghiệp vụ (BA) và thiết kế phần mềm.

---

## 3.1. Biểu đồ Tác nhân & Ca sử dụng (Use Case Diagram)
Mô tả những AI có quyền làm GÌ trên hệ thống, phân tách rõ ràng bằng quan hệ kế thừa.

```mermaid
graph TD
    %% Định nghĩa Actors
    subgraph Actors
        User[Người dùng Tổng quát]
        Owner[Quản lý / Chủ Project]
        System[Hệ thống Tự động]
    end

    Owner --> User

    subgraph SystemBoundary[Phạm vi Hệ thống Agentick]
        %% Use cases của User chung
        UC1((Đăng nhập / Đăng ký))
        UC2((Xem Bảng Kanban / List))
        UC3((Tạo / Sửa Công việc))
        UC4((Cập nhật Trạng thái Task))
        UC5((Ghi giờ thực hiện - Log time))
        
        %% Use cases của Quản lý
        UC6((Mời Thành viên mới))
        UC7((Tạo Dự án mới))
        UC8((Cấu hình Trạng thái & Mức ưu tiên))
        
        %% Các quan hệ hỗ trợ Include
        UC7_Inc((Tự tạo Status & Type mặc định))
        UC6_Inc((Gửi Email link bảo mật))
        
        %% System logic
        UC9((Quét rủi ro AI))
        UC10((Gửi mail báo nguy hiểm))
    end

    %% Nối Actor với Use Case
    User --- UC1
    User --- UC2
    User --- UC3
    User --- UC4
    User --- UC5

    Owner --- UC6
    Owner --- UC7
    Owner --- UC8

    %% Quan hệ include/extend
    UC7 -.->|include| UC7_Inc
    UC6 -.->|include| UC6_Inc
    
    System --- UC9
    UC9 -.->|extend: Score >= 0.7| UC10
```

---

## 3.2. Biểu đồ Lớp (Class Diagram)
Mô tả cấu trúc thực thể dữ liệu và các phương thức (methods) xử lý đi kèm.

```mermaid
classDiagram
    class User {
        +String id
        +String email
        +String name
        +String hashed_password
        +is_active() bool
    }
    
    class Project {
        +String id
        +String name
        +String timezone
        +Boolean is_deleted
    }

    class Task {
        +String id
        +String title
        +Float estimated_hours
        +Float actual_hours
        +DateTime due_date
        +is_overdue() bool
    }

    class BaseRepository {
        +create(schema) Object
        +read_by_id(id) Object
        +update(id, schema) Object
        +delete_by_id(id) void
    }

    class RiskAnalysisService {
        +analyze_task(task_id) RiskSnapshot
        +calculate_programmatic_signals(task) JSON
    }

    class ProjectService {
        +create_project(schema) Project
        +delete_project(project_id) void
        -_seed_project_catalogs(project_id) void
        -_ensure_user_in_team(team_id) void
    }

    Project "1" *-- "many" Task : chứa đựng
    User "1" --> "many" Project : tham gia
    RiskAnalysisService --> Task : phân tích
    ProjectService --> BaseRepository : sử dụng
```

---

## 3.3. Biểu đồ Hoạt động (Activity Diagram)
Lột tả luồng rẽ nhánh (Logic Decision) của tính năng lõi phức tạp nhất: Phân tích Rủi ro.

```mermaid
graph TD
    Start([Bắt đầu quét Task]) --> ReadInfo[1. Đọc thông tin Task & Hạn chót]
    ReadInfo --> PythonCalc[2. Chạy Python đếm giờ rảnh & mật độ]
    PythonCalc --> JSONBuild[3. Đóng gói số liệu thành JSON]
    JSONBuild --> AskLLM[4. Gửi JSON sang AI yêu cầu nhận xét]
    AskLLM --> AIAnswer{AI có trả kết quả?}
    
    AIAnswer -- Có --> SaveSnap[Lưu bảng RiskSnapshot]
    AIAnswer -- Không/Lỗi --> Fallback[Chạy logic dự phòng tính tay]
    Fallback --> SaveSnap
    
    SaveSnap --> ScoreCheck{Điểm Rủi ro >= 0.7?}
    
    ScoreCheck -- Đúng --> SendMail[Kích hoạt gửi Email cảnh báo]
    ScoreCheck -- Sai --> EndNode([Kết thúc an toàn])
    
    SendMail --> EndNode
```

---

## 3.4. Biểu đồ Tuần tự (Sequence Diagram)
Ghi lại lịch sử giao tiếp vượt tầng giữa các module của hệ thống.

### 3.4.1. Luồng Đăng ký & Chuẩn bị Dữ liệu (Auth Bootstrap)
```mermaid
sequenceDiagram
    autonumber
    actor User as Khách
    participant API as Cổng API
    participant SVC as Xử lý AuthService
    participant DB as CSDL (Postgres)

    User->>API: Nhập Email, Tên, Pass
    API->>SVC: sign_up()
    SVC->>DB: Lưu User & Mật khẩu
    SVC->>DB: Tự tạo Team & Project mặc định
    Note right of SVC: Logic ngầm sinh 6 Status + 5 Type
    SVC->>DB: Tạo Lịch cá nhân + Group
    SVC->>DB: COMMIT - Chốt lưu tất cả
    SVC-->>API: Trả UserInfo
    API-->>User: Đăng ký hoàn tất
```

### 3.4.2. Luồng Xử lý Agentic Tool (Actionable LLM)
Mô tả cách AI tự động chuyển đổi từ Chat thành Hành động viết xuống CSDL.

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant Agent as CustomAgent (Python)
    participant LLM as AI Core (OpenRouter)
    participant DB as Database Repository

    User->>Agent: Nhắn "Tạo task code API cho tôi"
    Agent->>LLM: Chuyển ngữ cảnh kèm danh sách Tool
    Note right of LLM: AI nhận diện yêu cầu sinh ra JSON hàm create_task()
    LLM-->>Agent: Trả về JSON Gọi hàm (Tool Calls)
    Agent->>DB: Thực thi create_task() vật lý xuống CSDL
    DB-->>Agent: Trả về ID Task mới
    Agent->>LLM: Nạp ID vừa tạo ngược vào lịch sử Chat
    LLM-->>Agent: Viết câu tổng kết: "Đã tạo Task xong cho bạn"
    Agent-->>User: Hiển thị câu trả lời cuối
```

---

## 3.5. Biểu đồ Thành phần & Triển khai (Physical Layout)

### 3.5.1. Sơ đồ Thành phần (Component)
```mermaid
graph LR
    UI[Giao diện App] --> Route[API Endpoints]
    Route --> Logic[Logic Tầng Service]
    Logic --> Data[Tầng Repository]
    Logic --> AI[Tầng AI Agent]
    Data --> DB[(Database)]
    AI --> API_Ext((Dịch vụ Ngoài))
```

### 3.5.2. Sơ đồ Triển khai (Deployment)
```mermaid
graph TD
    UserPC[Máy Laptop người dùng] -- Internet --> Docker[MÁY CHỦ DOCKER]
    subgraph Docker
        Node1[Frontend Container\nPort 3000]
        Node2[Backend Container\nPort 8000]
        Node3[DB Container\nPort 5432]
    end
    Node1 --> Node2
    Node2 --> Node3
    Node2 -- HTTPS --> AICloud((OpenRouter API))
```
