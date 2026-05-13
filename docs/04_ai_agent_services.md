# Tài liệu Kỹ thuật: Hệ thống Dịch vụ AI Agent - Agentick

Tài liệu này cung cấp cái nhìn tổng quan và chi tiết về các dịch vụ AI Agent hiện có trong dự án **Agentick**, bao gồm cả logic xử lý ngầm tại **Backend** (Python FastAPI) và trải nghiệm tương tác, hiển thị trực quan tại **Frontend** (React TanStack Start).

Hệ thống AI của Agentick được tích hợp xuyên suốt từ tầng hiển thị dashboard biểu đồ rủi ro, cảnh báo tại giao diện người dùng cho đến tầng lõi phân tích AI phía backend và các trình lập lịch background jobs.

---

## 1. Kiến trúc Tổng quan (High-Level Architecture)

Kiến trúc AI tuân theo mô hình hóa chiến lược (Strategy Pattern), cho phép thay đổi LLM backend linh hoạt thông qua `LLMStrategy` (hiện tại sử dụng `OpenRouterStrategy`).

```plantuml
@startuml
skinparam shadowing false
skinparam nodeBackgroundColor #F5F9FF
skinparam databaseBackgroundColor #FFFDF0
skinparam cloudBackgroundColor #F1FAF2
skinparam packageBackgroundColor #FFFFFF
skinparam ArrowColor #2563EB

left to right direction

' ========================
' TIER 4: EXTERNAL API
' ========================
cloud "External AI Providers" as EXT {
    [OpenRouter API] as OR_API
}

' ========================
' TIER 3: BACKEND LOGIC
' ========================
node "FastAPI Backend Node" as APP_NODE {
    package "AI Agent Services" {
        [AgentService] as AS
        [EstimationService] as ES
        [RiskAnalysisService] as RAS
        [AgentOutreachService] as AOS
    }
    
    package "Agentick Core" {
        [CustomAgent] as CA
    }
    
    package "Job Runner" {
        [APScheduler] as SCH
    }
}

' ========================
' TIER 2: FRONTEND INTERFACE
' ========================
node "Frontend Application Node\n(TanStack Start / React)" as FE_NODE {
    package "Agent Feature Modules" {
        [RiskDashboard Component] as RD
        [AIEstimationAlert Component] as AEA
    }
    package "Data Connectors" {
        [createServerFn / KyClient] as CONN
    }
}

' ========================
' TIER 1: PERSISTENCE LAYER
' ========================
node "Storage Layer" as STORE_NODE {
    database "PostgreSQL" as PG_DB
    database "Qdrant VectorDB" as QD_DB
}

' ======= FLOWS & RELATIONSHIPS =======

' FE to BE
RD -down-> CONN : fetch stats
AEA -down-> CONN : request est
CONN ..> AS : REST HTTP Call
CONN ..> ES : REST HTTP Call
CONN ..> RAS : REST HTTP Call

' BE Internal
AS -down-> CA : load prompt
RAS -down-> CA : scan data
AOS -down-> CA : email gen

' BE to Cloud
CA ..> OR_API : "HTTPS/JSON"

' BE to DB
ES -down-> QD_DB : "vector search"
ES -down-> PG_DB : "read history"
RAS -down-> PG_DB : "fetch signals"
AOS -down-> PG_DB : "read stale tasks"

' Scheduler
SCH -right-> RAS : "Auto Morning Run"

@enduml
```

---

## 2. Các Dịch vụ AI Agent Chi tiết

### 2.1 Agent Service (Trợ lý Tương tác Trực tiếp)

**Mô tả:**
Cung cấp một Chatbot thông minh có khả năng sử dụng công cụ (Tool Use/Function Calling) để thao tác trực tiếp với dữ liệu hệ thống (nhiệm vụ, dự án) theo yêu cầu tự nhiên của người dùng thông qua REST API.

**Codebase Liên quan:**
*   **Backend Logic:** `app/services/agent_service.py`, `app/agents/custom_agent.py`
*   **Frontend Integration:** Các components tương tác gọi API proxy hoặc server action.

#### Sequence Diagram: Luồng Tương tác Agent & Tool Calling

```plantuml
@startuml
skinparam shadowing false
skinparam ActorBackgroundColor #FFE082
skinparam ParticipantBackgroundColor #FFFFFF

actor "User" as USER

box "Frontend Layer" #F0F9FF
    participant "Chat UI Component" as FE
    participant "API Connector" as CONN
end box

box "Backend Layer" #FEFECE
    participant "AgentController" as CTRL
    participant "AgentService" as SVC
    participant "TaskTools" as TT
end box

box "AI / Cloud" #E8F5E9
    participant "CustomAgent" as CA
    participant "LLM Strategy" as LLM
end box

USER -> FE : Nhập Chat Prompt
activate FE
FE -> CONN : Call invokeAgentChat(prompt)
activate CONN
CONN -> CTRL : POST /api/v1/agent/run
activate CTRL
CTRL -> SVC : run_agent()
activate SVC
SVC -> CA : run(prompt, tools)
activate CA

group AI Call 1: Quyết định dùng Tool
    CA -> LLM : analyze_intent(messages, tools)
    activate LLM
    LLM --> CA : return [tool_calls_needed]
    deactivate LLM
end

alt NẾU AI cần dữ liệu hệ thống
    loop Mỗi Tool yêu cầu
        CA -> TT : execute_tool(name, args)
        activate TT
        TT --> CA : Dữ liệu trả về từ Database
        deactivate TT
    end
    
    group AI Call 2: Tổng hợp văn bản cuối
        CA -> LLM : generate_final_response(all_context)
        activate LLM
        LLM --> CA : return plain_text_response
        deactivate LLM
    end
end

CA --> SVC : Phản hồi hoàn tất
deactivate CA
SVC --> CTRL : Dữ liệu JSON
deactivate SVC
CTRL --> CONN : 200 OK JSON
deactivate CTRL
CONN --> FE : Trả về Response
deactivate CONN
FE --> USER : Hiển thị tin nhắn AI lên màn hình
deactivate FE

@enduml
```

---

### 2.2 Estimation Service (Ước lượng Thời gian Thông minh)

**Mô tả:**
Thực hiện ước lượng thời gian (`estimated_hours`) cho một Task mới dựa trên mô hình **Case-Based Reasoning (CBR)** kết hợp RAG. Dịch vụ này truy xuất các task tương tự trong quá khứ từ Qdrant Vector DB, phân tích độ lệch thời gian thực tế và nhờ AI dự đoán. 

Phía Frontend hiển thị lý do giải thích chi tiết sự lựa chọn thời gian của AI để tăng tính minh bạch.

**Codebase Liên quan:**
*   **Backend Service:** `app/services/estimation_service.py`
*   **Frontend Component:** `features/tasks/components/task-table/task-ai-estimation-alert.tsx` (Dùng hiển thị reasoning_steps: similarity & variance analysis)

#### Use Case & Flow Diagram

```plantuml
@startuml
skinparam shadowing false
skinparam ActorBackgroundColor #FFE082

actor "User / Manager" as USER

box "Frontend Layer" #F0F9FF
    participant "Task Input Form" as FE
    participant "API Connector" as CONN
end box

box "Backend Layer" #FEFECE
    participant "EstimationService" as ES
end box

box "Data Layer" #FFFDF0
    database "Qdrant VectorDB" as VEC
    database "Postgres SQL" as DB
end box

box "AI / Cloud" #E8F5E9
    participant "LLM Strategy" as LLM
end box

USER -> FE : Nhập thông tin Task mới
activate FE
FE -> CONN : Trigger AutoEstimate()
activate CONN
CONN -> ES : POST /estimate(title, desc)
activate ES

ES -> VEC : search_similar_tasks()
activate VEC
note right: Tìm cases quá khứ tương đồng
VEC --> ES : List Similar IDs
deactivate VEC

ES -> DB : get_tasks_by_ids()
activate DB
DB --> ES : Trả về data thời gian thực tế
deactivate DB

ES -> LLM : generate_chat_completion(CBR Prompt)
activate LLM
LLM --> ES : Return JSON {suggested_hours, rationale}
deactivate LLM

ES --> CONN : JSON Result
deactivate ES
CONN --> FE : Update Local State
deactivate CONN
FE -> FE : Render TaskAIEstimationAlert
FE --> USER : Hiển thị gợi ý giờ & Giải thích logic
deactivate FE

@enduml
```

---

### 2.3 Risk Analysis Service (Phân tích & Cảnh báo Rủi ro)

**Mô tả:**
Một dịch vụ "Hybrid" kết hợp giữa các thuật toán xác định (Deterministic) và AI tổng hợp. Hệ thống tự động tính toán các chỉ số rủi ro (Tiến độ, Trễ lịch trình, Xung đột tải công việc), sau đó chuyển cho AI Agent để đưa ra đánh giá rủi ro chi tiết và các khuyến nghị quản lý (Managerial recommendations).

Phía Frontend tổng hợp dữ liệu snapshot rủi ro và hiển thị qua Dashboard trực quan sử dụng `recharts` (Radar, Scatter plots, v.v.).

**Codebase Liên quan:**
*   **Backend Service:** `app/services/risk_analysis_service.py`
*   **Frontend Feature:** `features/agent/components/*`
    *   `project-risk-dashboard.tsx`: Tổng quan dashboard.
    *   `risk-matrix-chart.tsx`: Phân bổ rủi ro dạng scatter plot.
    *   `risk-drivers-chart.tsx`: Biểu đồ radar phân tích yếu tố rủi ro.

#### Sequence Diagram: Luồng Phân tích Rủi ro tự động

```plantuml
@startuml
skinparam shadowing false
skinparam ActorBackgroundColor #FFE082

actor "User / Manager" as USER

box "Frontend Layer" #F0F9FF
    participant "Risk Dashboard UI" as FE
    participant "API Connector" as CONN
end box

box "Backend Layer" #FEFECE
    participant "RiskAnalysisService" as RAS
end box

box "Data Layer" #FFFDF0
    database "Postgres SQL" as DB
end box

box "AI / Cloud" #E8F5E9
    participant "CustomAgent" as CA
    participant "LLM Strategy" as LLM
end box

participant "Notification Service" as MAIL #F3E5F5

USER -> FE : Truy cập Dashboard / Xem Chi tiết
activate FE
FE -> CONN : fetchProjectRiskStats()
activate CONN
CONN -> DB : Lấy Snapshot gần nhất
activate DB
DB --> FE : Dữ liệu có sẵn
deactivate DB

== Luồng Tự động Quét (Trigger ngầm) ==
[-> RAS : invoke analyze_task(task_id)
activate RAS
RAS -> DB : Lấy Task Data, Checkpoints & Schedule
activate DB
DB --> RAS : Source Data
deactivate DB

note over RAS: 1. Chạy Programmatic Code:\nTính Variance, Schedule Bottleneck, Congestion

RAS -> CA : Tổng hợp context và gọi AI
activate CA
CA -> LLM : analyze_signals_and_recommend(JSON)
activate LLM
LLM --> CA : JSON Result
deactivate LLM
CA --> RAS : Kết quả
deactivate CA

RAS -> DB : Tạo RiskSnapshot ghi vào bảng
activate DB
DB --> RAS : Success
deactivate DB

alt NẾU Risk Score >= 0.7 (Critical)
    RAS -> MAIL : send_risk_alert_email(Assignees)
    activate MAIL
    MAIL --> RAS : Gửi thành công
    deactivate MAIL
    RAS -> DB : update snapshot.alert_sent = True
end
deactivate RAS

CONN --> FE : Trả về các snapshot mới nhất
deactivate CONN
FE -> FE : Recharts render: RiskMatrix, Drivers Radar
FE --> USER : Hiển thị đồ thị phân tích rủi ro hiện tại
deactivate FE

@enduml
```

---

### 2.4 Các Dịch vụ Chạy Ngầm (Silent Services)

Hệ thống bao gồm hai cơ chế chạy ngầm chính vận hành bởi **APScheduler** kết hợp cùng các logic AI để tự động hóa việc theo dõi dự án:

#### A. Scheduler & Risk Management Lifecycle

**Mô tả:**
Bộ lập lịch `app/core/scheduler.py` đảm bảo việc phân tích rủi ro diễn ra tự động vào đầu ngày và báo cáo tổng hợp vào cuối ngày, căn cứ chính xác theo **Timezone** của từng dự án.

1.  **Morning Scan Job (9:00 AM Local Time):** Duyệt qua tất cả tasks chưa hoàn thành, nếu giờ địa phương của project là 9h sáng, tự động gọi `RiskAnalysisService.analyze_task` bất đồng bộ.
2.  **Evening Summary Job (5:30 PM Local Time):** Quét các Snapshot rủi ro được tạo ra trong ngày, lọc các rủi ro >= 0.5, tạo template HTML báo cáo và gửi email trực tiếp đến Team Lead.

#### B. Agent Outreach Service (Chăm sóc & Nhắc nhở tự động)

**Mô tả:**
Dịch vụ này hoạt động như một "Quản lý ảo" đi rà soát hệ thống. Khi phát hiện dữ liệu task bị hụt (ví dụ: thiếu giờ ước tính) hoặc task đã quá lâu không có hoạt động (stale updates), dịch vụ sẽ nhờ AI soạn một email nhắc nhở thân thiện, cá nhân hóa để gửi tới Assignee.

**Sử dụng:** `app/services/agent_outreach_service.py`

#### Sequence Diagram: Luồng Chăm sóc & Gửi Mail nhắc nhở

```plantuml
@startuml
skinparam shadowing false

box "Background Services" #FDFD96
    control "APScheduler" as SCH
    participant "OutreachService" as OS
end box

box "Data Layer" #FFFDF0
    database "Postgres SQL" as DB
end box

box "AI Layer" #E8F5E9
    participant "CustomAgent" as CA
    participant "LLM Strategy" as LLM
end box

participant "Mail Transfer Agent" as SMTP #F3E5F5

SCH -> OS : Kích hoạt cycle theo lịch
activate OS

OS -> DB : Quét tasks active & chưa hoàn thành
activate DB
DB --> OS : Data Tasks
deactivate DB

loop Duyệt qua từng Task
    OS -> OS : Chạy evaluate(Anti-Spam + Stale Check)
    
    alt Thỏa mãn điều kiện gửi Remind
        OS -> CA : Soạn email context cho user
        activate CA
        CA -> LLM : Viết mail thân thiện (Max 5 sentences)
        activate LLM
        LLM --> CA : Email Content Body
        deactivate LLM
        CA --> OS : Text data
        deactivate CA
        
        OS -> SMTP : Dispatch email(Content, Receiver)
        activate SMTP
        SMTP --> OS : Dispatch Success
        deactivate SMTP
        
        OS -> DB : insert log AgentOutreach & RiskSnapshot
    end
end

[<-- OS : Cycle complete
deactivate OS

@enduml
```

### Tổng hợp các API Trigger cho Background Services

Các dịch vụ ngầm này cũng được expose qua route `/api/v1/agent/` để quản trị viên có thể trigger cưỡng bức ngay lập tức phục vụ demo hoặc xử lý khẩn cấp:
*   `POST /agent/outreaches`: Kích hoạt vòng quét outreach gửi mail nhắc nhở.
*   `POST /agent/morning-scan/trigger`: Cưỡng bức chạy quét rủi ro sáng sớm toàn hệ thống.
*   `POST /agent/evening-summary/trigger`: Gửi báo cáo tổng hợp chiều tối tới Team Lead ngay lập tức.

---
*Tài liệu này được trích xuất và hệ thống hóa tự động dựa trên codebase hiện tại của Agentick.*
