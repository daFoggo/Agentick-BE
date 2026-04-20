# Hướng dẫn Tích hợp Frontend — Cross-Team Work Calendar

Hệ thống đã hỗ trợ khả năng **Tổng hợp lịch trình từ nhiều Team**. Mỗi sự kiện (Event) được gắn với cả một Team (ngữ cảnh) và một User (người thực hiện).

---

## 1. Luồng của Tôi (Lịch Tổng hợp - My Global Calendar)

Mục đích: User muốn thấy tất cả công việc của mình trên tất cả các Team.

- **API**: `GET /api/v1/events/me?start_date=...&end_date=...`
- **Cơ chế**: Backend sẽ quét tất cả các sự kiện bận rộn (`task_block`, `meeting`, v.v.) có `user_id` là bạn, bất kể nó thuộc Team nào.
- **Cách dùng**: Vẽ lên Big Calendar cá nhân của User để họ có cái nhìn tổng quát về workload của mình trong toàn bộ workspace.

---

## 2. Luồng Team (Lịch Dashboard của Team)

Mục đích: Admin hoặc Member xem lịch trình của các thành viên trong nội bộ 01 Team cụ thể.

- **API**: `GET /api/v1/events/teams/{team_id}?start_date=...&end_date=...`
- **Cơ chế**: Trả về tất cả sự kiện có `team_id` khớp với yêu cầu.
- **Cách dùng**: Hiển thị trên Dashboard Team để xem tiến độ và sự sẵn sàng của các thành viên trong bối cảnh Team đó.

---

## 3. Đồng bộ Task tự động

- Khi một Task được giao (assign) cho bạn trong Project X thuộc Team A:
    - Backend tự động tạo một Event trên Lịch.
    - Event này sẽ có `team_id = A` và `user_id = bạn`.
- Khi bạn xem Lịch Global, Event này sẽ hiện ra. Khi Admin xem Lịch Team A, Event này cũng hiện ra.

---

> [!IMPORTANT]
> **Điểm mới:** `user_id` và `team_id` giờ đây là các trường cốt lõi của Event. 
> - Khi bạn tạo sự kiện thủ công (ví dụ họp), hãy đảm bảo truyền đúng `team_id` để sự kiện đó xuất hiện đúng ngữ cảnh.
> - `calendar_id` vẫn tồn tại nhưng đóng vai trò là "vỏ bọc" vật lý, việc quản lý truy cập và tổng hợp chủ yếu dựa trên `user_id` và `team_id`.