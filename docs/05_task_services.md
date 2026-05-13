# Tài liệu Kỹ thuật: Quy trình CRUD Tác vụ (Task Core Operations) - Agentick

Tài liệu này mô tả chi tiết 4 thao tác cốt lõi (Create, Read, Update, Delete) của hệ thống quản lý Task, nhấn mạnh sự liên kết với các hệ thống bên ngoài (Qdrant, Notifications).

---

## 1. Quy trình Tạo mới (CREATE)

**Đặc điểm:** Lưu dữ liệu Transactional vào SQL và đồng bộ ngữ nghĩa (Semantic content) sang Qdrant Vector DB chạy ngầm để phục vụ AI RAG.

```plantuml
@startuml
skinparam shadowing false
skinparam ActorBackgroundColor #FFE082

actor "User" as USER

box "Frontend Layer" #F0F9FF
    participant "Task Form UI" as FE
    participant "API Connector" as CONN
end box

box "Backend Layer" #FEFECE
    participant "TaskController" as CTRL
    participant "TaskRepository" as REPO
end box

box "Data Layer" #FFFDF0
    database "Postgres SQL" as SQL
end box

participant "Qdrant Vector DB" as VEC #E8F5E9

USER -> FE : Fill & Submit Task
activate FE
FE -> CONN : Request POST
activate CONN
CONN -> CTRL : invoke create()
activate CTRL
CTRL -> REPO : execute create()
activate REPO

REPO -> SQL : Insert Task, Set Lead Member
activate SQL
SQL --> REPO : Return Data
deactivate SQL

note over REPO : Spawn background thread

REPO --> CTRL : Task Object
deactivate REPO
CTRL --> CONN : 201 Created
deactivate CTRL
CONN --> FE : Render Success UI
deactivate CONN
FE --> USER : Hiện Task mới
deactivate FE

== Background Sync ==
REPO -> VEC : Upsert semantic vector
@enduml
```

---

## 2. Quy trình Đọc dữ liệu (READ)

**Đặc điểm:** Hỗ trợ load danh sách kèm tính năng `Eager Load` để tự động nạp thông tin người đại diện, phase và độ ưu tiên trong duy nhất một câu query JOIN.

```plantuml
@startuml
skinparam shadowing false
skinparam ActorBackgroundColor #FFE082

actor "User" as USER

box "Frontend Layer" #F0F9FF
    participant "List / Board View" as FE
    participant "API Connector" as CONN
end box

box "Backend Layer" #FEFECE
    participant "TaskRepository" as REPO
end box

box "Data Layer" #FFFDF0
    database "Postgres SQL" as SQL
end box

USER -> FE : Mở trang dự án
activate FE
FE -> CONN : fetchTasks()
activate CONN
CONN -> REPO : read_by_options(eager=True)
activate REPO

REPO -> SQL : SELECT with JOINs (Status, Priority, Member)
activate SQL
SQL --> REPO : Graph objects
deactivate SQL

REPO --> CONN : Json Payload
deactivate REPO
CONN --> FE : Set Global State
deactivate CONN
FE --> USER : Vẽ Kanban / Bảng dữ liệu
deactivate FE

@enduml
```

---

## 3. Quy trình Cập nhật (UPDATE)

**Đặc điểm:** Đây là luồng phức tạp nhất. Hệ thống tự động diff dữ liệu để ghi **Audit Log** vào bảng `TaskActivity`, đồng thời nếu đổi người được giao, hệ thống tự bắn **Notification** và re-sync vector.

```plantuml
@startuml
skinparam shadowing false
skinparam ActorBackgroundColor #FFE082

actor "User" as USER

box "Frontend Layer" #F0F9FF
    participant "Detail View" as FE
    participant "API Connector" as CONN
end box

box "Backend Layer" #FEFECE
    participant "TaskRepository" as REPO
end box

box "Data Layer" #FFFDF0
    database "Postgres SQL" as SQL
end box

participant "System Notifications" as NOTIF #F3E5F5
participant "Qdrant Vector DB" as VEC #E8F5E9

USER -> FE : Thay đổi Status / Member
activate FE
FE -> CONN : PATCH request
activate CONN
CONN -> REPO : update(id, patch_data)
activate REPO

REPO -> SQL : Compare old vs new data
activate SQL
SQL --> REPO : Diff ready
deactivate SQL

note over REPO : 1. Tự điền Completed Timestamp if Done
REPO -> SQL : 2. Insert 'TaskActivity' audit entry
REPO -> SQL : 3. Commit Task update

alt NẾU MEMBER DANH SÁCH THAY ĐỔI
    REPO -> NOTIF : create_task_assignment_notifications()
end

REPO --> CONN : Updated Object
deactivate REPO
CONN --> FE : Refresh UI state
deactivate CONN
FE --> USER : View Update success
deactivate FE

== Background Async ==
REPO -> VEC : Update vector index if content changed
@enduml
```

---

## 4. Quy trình Xóa (DELETE)

**Đặc điểm:** Xóa vật lý bản ghi khỏi PostgreSQL (Cascade delete task_members theo cấu hình DB).

```plantuml
@startuml
skinparam shadowing false
skinparam ActorBackgroundColor #FFE082

actor "User" as USER

box "Frontend Layer" #F0F9FF
    participant "Delete Dialog" as FE
    participant "API Connector" as CONN
end box

box "Backend Layer" #FEFECE
    participant "TaskController" as CTRL
    participant "TaskRepository" as REPO
end box

box "Data Layer" #FFFDF0
    database "Postgres SQL" as SQL
end box

USER -> FE : Xác nhận xóa
activate FE
FE -> CONN : DELETE /tasks/{id}
activate CONN
CONN -> CTRL : invoke delete()
activate CTRL
CTRL -> REPO : delete_by_id()
activate REPO

REPO -> SQL : DELETE FROM tasks WHERE id=...
activate SQL
SQL --> REPO : Row Removed
deactivate SQL

REPO --> CTRL : Success status
deactivate REPO
CTRL --> CONN : 204 No Content
deactivate CTRL
CONN --> FE : Remove row from view
deactivate CONN
FE --> USER : Màn hình ẩn task đã xóa
deactivate FE

@enduml
```
