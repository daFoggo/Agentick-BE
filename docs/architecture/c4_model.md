# Đặc tả Kiến trúc Hệ thống Agentick (C4 Model)

Tài liệu này mô tả chi tiết kiến trúc của nền tảng quản lý công việc tích hợp AI **Agentick**, được phân rã thành 3 cấp độ (System Context, Containers, Components) theo mô hình chuẩn C4 Model. Tài liệu bám sát 100% mã nguồn thực tế của dự án Frontend (React 19 / TanStack Start) và Backend (FastAPI / Python 3.12).

---

## LEVEL 1: SYSTEM CONTEXT (BẢN VẼ NGỮ CẢNH HỆ THỐNG)

Mô tả mối quan hệ giữa Người dùng, Hệ thống Agentick và các Hệ thống ngoại vi (bên thứ ba) ở mức cao nhất nhằm cung cấp góc nhìn tổng quan (Big Picture).

### 1. Sơ đồ Ngữ cảnh hệ thống (System Context Diagram)

```mermaid
graph TD
    PM["Project Manager (Person)"] -- "Lập kế hoạch & Giám sát rủi ro" --> Agentick["Agentick System (Software System)"]
    TM["Team Member (Person)"] -- "Cập nhật tiến độ & Lịch cá nhân" --> Agentick
    
    Agentick -- "Yêu cầu phân tích rủi ro & Ước lượng [HTTPS]" --> AI["AI Reasoning - OpenRouter (External System)"]
    Agentick -- "Gửi thư mời & Báo cáo tóm tắt [SMTP]" --> Email["Email Delivery System (External System)"]
    Agentick -- "Ghi nhận vết hoạt động AI (Traces) [HTTPS]" --> Opik["AI Monitoring - Opik (External System)"]

    style Agentick fill:#003366,stroke:#fff,stroke-width:2px,color:#fff
    style PM fill:#00509d,stroke:#fff,color:#fff
    style TM fill:#00509d,stroke:#fff,color:#fff
    style AI fill:#4b5563,stroke:#fff,color:#fff
    style Email fill:#4b5563,stroke:#fff,color:#fff
    style Opik fill:#4b5563,stroke:#fff,color:#fff
```

### 2. Đặc tả các phần tử cốt lõi
* **Con người (Actors):**
  * **Project Manager (Quản lý dự án):** Người lập kế hoạch, phân công công việc, giám sát tiến độ dự án và theo dõi các cảnh báo rủi ro trễ hạn từ AI.
  * **Team Member (Thành viên):** Người thực thi công việc, cập nhật tiến độ task và khai báo lịch trình làm việc cá nhân.
* **Hệ thống phần mềm trung tâm (Software System):**
  * **Agentick System:** Nền tảng quản lý dự án tích hợp AI Agent chủ động phân tích rủi ro và tối ưu hóa vận hành.
* **Hệ thống ngoại vi (External Systems):**
  * **OpenRouter (AI Reasoning):** Cổng kết nối API cung cấp các mô hình ngôn ngữ lớn (mặc định `openai/gpt-4o-mini`) để thực hiện các phân tích rủi ro và ước lượng deadline.
  * **Opik (AI Monitoring):** Nền tảng giám sát AI, theo dõi chi tiết các traces/spans chạy ngầm của AI Agent nhằm tối ưu hóa chi phí token và hiệu suất.
  * **Email Delivery System:** Dịch vụ gửi email (SMTP) hỗ trợ phân phối thư mời thành viên và báo cáo rủi ro hàng ngày.

---

## LEVEL 2: CONTAINER (BẢN VẼ THÀNH PHẦN CHẠY ĐỘC LẬP)

Mô tả các thành phần chạy độc lập (containers) cấu thành nên hệ thống Agentick, chỉ rõ ranh giới công nghệ và các giao thức giao tiếp vật lý.

### 1. Sơ đồ Container (Container Diagram)

```mermaid
graph TB
    subgraph Users ["Người dùng"]
        U["Project Manager & Team Member"]
    end

    subgraph Agentick_System ["Ranh giới Hệ thống Agentick"]
        FE["Web App Container<br>[React 19 / TanStack Start]<br><br>Giao diện người dùng SSR/SPA, quản lý định tuyến, UI Dashboard rủi ro và lịch biểu."]
        
        BE["API Application Container<br>[FastAPI / Python 3.12]<br><br>Xử lý nghiệp vụ chính, bảo mật, xác thực JWT, chạy các dịch vụ AI Agent Core."]
        
        SCHED["Background Scheduler Container<br>[APScheduler (In-Process)]<br><br>Lập lịch chạy ngầm in-process: Quét rủi ro 9:00 AM và gửi email báo cáo 5:30 PM."]
        
        DB["Relational Database Container<br>[PostgreSQL 18]<br><br>Lưu trữ dữ liệu quan hệ có cấu trúc (User, Task, Project, Team, logs)."]
        
        VDB["Vector Database Container<br>[Qdrant]<br><br>Lưu trữ vector embeddings để tìm kiếm ngữ nghĩa tương đồng (RAG) cho AI Agent."]
    end

    subgraph External ["Hệ thống ngoại vi"]
        OpenRouter["OpenRouter API (gpt-4o-mini)"]
        SMTP["Email Service (SMTP)"]
        Opik["Opik Platform"]
    end

    U -- "Tương tác [HTTPS]" --> FE
    FE -- "Gọi API [REST / JSON]" --> BE
    BE -- "Kích hoạt định kỳ [In-process]" --> SCHED
    BE -- "Đọc/Ghi dữ liệu [SQL / SQLAlchemy ORM]" --> DB
    BE -- "Tìm kiếm ngữ nghĩa [REST / HTTP]" --> VDB
    
    BE -- "Gửi prompt phân tích [HTTPS / REST]" --> OpenRouter
    BE -- "Gửi mail báo cáo [SMTP]" --> SMTP
    BE -- "Gửi trace telemetry [HTTPS / REST]" --> Opik

    style FE fill:#2563eb,stroke:#fff,color:#fff
    style BE fill:#2563eb,stroke:#fff,color:#fff
    style SCHED fill:#1d4ed8,stroke:#fff,color:#fff
    style DB fill:#1e3a8a,stroke:#fff,color:#fff
    style VDB fill:#1e3a8a,stroke:#fff,color:#fff
```

### 2. Đặc tả kỹ thuật các Containers
* **Web App (SPA / SSR):** React 19 + TanStack Start. Cung cấp UI lịch làm việc, quản lý công việc và báo cáo tổng quan. Chạy trực tiếp trên trình duyệt của người dùng.
* **API Application:** FastAPI (Python 3.12) chạy trên máy chủ. Điểm tiếp nhận trung tâm của toàn bộ logic nghiệp vụ qua các API endpoints RESTful.
* **Background Scheduler:** APScheduler. Thư viện lập lịch chạy ngầm **in-process** (cùng tiến trình Backend) để thực hiện quét rủi ro (9:00 AM) và báo cáo (5:30 PM) theo múi giờ riêng của từng dự án.
* **Relational Database:** PostgreSQL 18. Lưu trữ dữ liệu quan hệ có cấu trúc của hệ thống, kết nối qua SQLAlchemy ORM.
* **Vector Database:** Qdrant. Lưu trữ các vector embeddings để phục vụ tìm kiếm ngữ nghĩa cho AI Agent (RAG).

---

## LEVEL 3: COMPONENT (CHI TIẾT LOGIC MÃ NGUỒN)

Zoom chi tiết vào cấu trúc tổ chức mã nguồn thực tế của hai Container chính là **API Application (Backend)** và **Web App (Frontend)**.

### 1. Phân rã Component trong API Application (Backend - FastAPI)

Sơ đồ mô tả cấu trúc thư mục của dự án `Agentick-BE` và mối liên kết nghiệp vụ:

```mermaid
graph TB
    subgraph FE_Container ["External Web App Container"]
        FE["SPA/SSR Web Application<br>(React 19 / TanStack Start)"]
    end

    subgraph API_Container ["API Application Container (FastAPI)"]
        RC["Route Controllers<br>(app/api/v1/endpoints/)<br><br>Định nghĩa API Routes, validate schema đầu vào/đầu ra, phân quyền HTTP."]
        
        CS["Core & Security<br>(app/core/)<br><br>Quản lý cấu hình (config.py), DB session lifecycle, JWT Auth và Middleware."]
        
        BS["Business Services<br>(app/services/)<br><br>Xử lý logic nghiệp vụ, phối hợp dữ liệu các Repositories, quản lý transaction (Unit of Work)."]
        
        DR["Data Repositories<br>(app/repository/)<br><br>Thực hiện truy vấn SQL/ORM để đọc/ghi cơ sở dữ liệu PostgreSQL."]
        
        AR["AI Agent Runtime<br>(app/agents/ & app/tools/)<br><br>Định nghĩa AI Agent, điều phối LLM calls, quản lý tracing và thực thi Agent Tools."]
    end

    subgraph Other_Containers ["Other Containers & External Systems"]
        SCHED["Background Scheduler<br>(APScheduler)"]
        DB["Relational Database<br>(PostgreSQL 18)"]
        VDB["Vector Database<br>(Qdrant)"]
        OpenRouter["OpenRouter API<br>(gpt-4o-mini)"]
        SMTP["Email Service<br>(SMTP)"]
        Opik["Opik Platform<br>(Agent Tracking)"]
    end

    %% Giao tiếp ngoại vi vào API
    FE -- "Gọi API [REST/HTTPS]" --> RC
    SCHED -- "Kích hoạt tác vụ ngầm [In-process]" --> BS

    %% Giao tiếp nội bộ Container
    RC -- "Sử dụng cấu hình [FastAPI Depends]" --> CS
    RC -- "Gọi nghiệp vụ [Method calls]" --> BS
    BS -- "Yêu cầu xử lý AI [Method calls]" --> AR
    BS -- "Đọc/Ghi dữ liệu [Method calls]" --> DR
    BS -- "Gửi email thông báo [SMTP]" --> SMTP

    %% Giao tiếp từ API ra ngoài
    DR -- "Truy vấn [SQLAlchemy]" --> DB
    AR -- "Tìm kiếm vector [REST]" --> VDB
    AR -- "Gửi prompt [HTTPS]" --> OpenRouter
    AR -- "Gửi logs trace [HTTPS]" --> Opik

    style API_Container fill:none,stroke:#003366,stroke-width:2px,stroke-dasharray: 5 5
    style RC fill:#2563eb,stroke:#fff,color:#fff
    style CS fill:#2563eb,stroke:#fff,color:#fff
    style BS fill:#2563eb,stroke:#fff,color:#fff
    style DR fill:#2563eb,stroke:#fff,color:#fff
    style AR fill:#2563eb,stroke:#fff,color:#fff
```

#### Đặc tả chi tiết các Components phía Backend (FastAPI):
* **Route Controllers (`app/api/v1/endpoints/`):**
  * *Nhiệm vụ:* Định nghĩa các đường dẫn HTTP (ví dụ: `projects.py`, `tasks.py`, `agent.py`, `teams.py`). Tiếp nhận request, xác thực quyền truy cập HTTP và bọc kết quả trả về trong schema cấu trúc `ResponseSchema` chuẩn hóa.
  * *Mã nguồn thực tế:* Sử dụng FastAPI `Depends` để tiêm các dịch vụ nghiệp vụ cần thiết.
* **Core & Security (`app/core/`):**
  * *Nhiệm vụ:* Quản lý cấu hình config qua Pydantic Settings (`config.py`). Quản lý xác thực JWT và phân quyền (`security.py`). Cung cấp DB session `get_db()` dùng chung trong vòng đời request (`dependencies.py`).
* **Business Services (`app/services/`):**
  * *Nhiệm vụ:* Trái tim xử lý nghiệp vụ chính của hệ thống.
  * *Mã nguồn thực tế:* `risk_analysis_service.py` điều phối quy trình phân tích rủi ro của task; `estimation_service.py` phối hợp ước lượng deadline; `invitation_service.py` xử lý logic tạo và gửi thư mời thành viên.
* **Data Repositories (`app/repository/`):**
  * *Nhiệm vụ:* Đóng gói toàn bộ các thao tác truy vấn cơ sở dữ liệu quan hệ (PostgreSQL).
  * *Mã nguồn thực tế:* `user_repository.py`, `task_repository.py`, `project_repository.py` kế thừa từ `BaseRepository` của SQLAlchemy, tránh rò rỉ logic HTTP hoặc nghiệp vụ xuống database.
* **AI Agent Runtime (`app/agents/` & `app/tools/`):**
  * *Nhiệm vụ:* Môi trường thực thi của Agentic AI.
  * *Mã nguồn thực tế:*
    * `llm_strategy.py`: Định nghĩa Interface `LLMStrategy` và triển khai lớp cụ thể `OpenRouterStrategy`.
    * `custom_agent.py`: Khởi tạo thực thể AI Agent, điều phối prompt, gọi các công cụ bổ trợ (`app/tools/task_tools.py`) để thu thập dữ liệu và tích hợp decorator `@track` của **Opik** phục vụ tracing.

---

### 2. Phân rã Component trong Web App (Frontend - React 19 / TanStack)

Frontend (`Agentick-FE`) được cấu trúc theo mô hình **Feature-based**, tự đóng gói các logic nghiệp vụ theo từng module tính năng:

```mermaid
graph TB
    subgraph FE_App ["Web App Container (React 19)"]
        RT["Routing Layer<br>(src/routes/ & src/router.tsx)<br><br>Điều hướng trang bằng TanStack Router, cấu hình lazy-loading."]
        
        ST["Global Stores<br>(src/stores/)<br><br>Quản lý trạng thái client toàn cục bằng Zustand (Auth state, UI theme)."]
        
        subgraph Feature_Modules ["Features Module (src/features/[feature]/)"]
            UI["UI Components<br>(components/)<br><br>Atoms & Layout vẽ UI dùng Tailwind v4 và shadcn/ui."]
            
            Q["Query & Mutation Layer<br>(queries.ts)<br><br>Quản lý Server State, cơ chế Caching bằng TanStack Query."]
            
            SC["Ky HTTP Client API<br>(server.ts)<br><br>Đóng gói các hàm gọi API REST thực tế tới Backend thông qua Ky v2."]
            
            VAL["Validation Layer<br>(schemas.ts)<br><br>Validate định dạng form và data phía client sử dụng Zod."]
        end
    end

    RT -- "Sử dụng" --> ST
    RT -- "Render" --> UI
    UI -- "Kích hoạt" --> Q
    Q -- "Gọi hàm" --> SC
    Q -- "Validate bằng" --> VAL

    style Feature_Modules fill:none,stroke:#1e40af,stroke-width:1px,stroke-dasharray: 3 3
    style RT fill:#0284c7,stroke:#fff,color:#fff
    style ST fill:#0284c7,stroke:#fff,color:#fff
    style UI fill:#0284c7,stroke:#fff,color:#fff
    style Q fill:#0284c7,stroke:#fff,color:#fff
    style SC fill:#0284c7,stroke:#fff,color:#fff
    style VAL fill:#0284c7,stroke:#fff,color:#fff
```

#### Đặc tả chi tiết các Components phía Frontend (React 19):
* **Routing Layer (`src/routes/`):** Sử dụng **TanStack Router**. File `routeTree.gen.ts` được tự động sinh ra dựa trên cấu trúc thư mục vật lý trong `src/routes/` (như trang `/dashboard`, `/projects`, `/tasks`).
* **Global Stores (`src/stores/`):** Sử dụng **Zustand** để đồng bộ trạng thái đăng nhập của người dùng (`authStore`) và cấu hình giao diện.
* **Feature Modules (`src/features/[feature]/`):** Chia nhỏ ứng dụng thành các module tính năng độc lập (như `projects`, `tasks`, `teams`, `inbox`). Mỗi module tự đóng gói:
  * `components/`: UI cụ thể của tính năng được vẽ dựa trên nền tảng **Tailwind CSS v4** và **shadcn/ui**.
  * `queries.ts`: Cấu hình các API Queries và Mutations sử dụng **TanStack Query** để quản lý caching, tối ưu hóa request và đồng bộ hóa trạng thái tức thì với Backend.
  * `server.ts`: Sử dụng thư viện **Ky v2** để định nghĩa các hàm gửi request lên Backend API.
  * `schemas.ts`: Sử dụng **Zod** để định nghĩa schema và validate dữ liệu form trước khi gửi lên Backend.

---

## BẢNG MA TRẬN KẾT NỐI VÀ GIAO THỨC (INTERFACE MATRIX)

Đặc tả chi tiết toàn bộ các cổng giao tiếp vật lý và luồng dữ liệu truyền nhận trong hệ thống Agentick:

| STT | Container Nguồn | Container Đích | Giao thức (Protocol) | Cổng (Port) | Bản chất dữ liệu truyền nhận |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Client Browser | Web App (SPA/SSR) | HTTP / HTTPS | `80` / `443` | Tải tài nguyên tĩnh (HTML, JS, CSS, Media). |
| **2** | Web App (SPA/SSR) | API Application | REST / HTTPS | `8000` | Gửi payload JSON yêu cầu nghiệp vụ (CRUD, Auth, trigger AI). |
| **3** | API Application | Relational DB | SQL (SQLAlchemy) | `5432` | Đọc/ghi thông tin người dùng, công việc, dự án, token log. |
| **4** | API Application | Vector DB | REST / HTTP | `6333` | Lưu trữ vector embeddings và truy vấn tìm kiếm ngữ nghĩa. |
| **5** | API Application | Background Scheduler | In-process Async calls | N/A | Điều phối kích hoạt các jobs (`morning_scan`, `evening_summary`). |
| **6** | API Application | OpenRouter (AI) | REST / HTTPS | `443` | Gửi prompt phân tích rủi ro, nhận điểm số và khuyến nghị AI. |
| **7** | API Application | Opik (Monitoring) | REST / HTTPS | `443` | Đẩy dữ liệu telemetry tracking LLM (Input/Output tokens, latency). |
| **8** | API Application | Email Service (SMTP) | SMTP (STARTTLS) | `587` | Gửi HTML Email báo cáo rủi ro công việc và thư mời thành viên. |
