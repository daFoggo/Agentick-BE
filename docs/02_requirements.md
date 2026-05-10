# 2. Đặc tả Yêu cầu Hệ thống (Requirements)

Tài liệu này mô tả thực tế những người dùng tham gia vào hệ thống và các tính năng cụ thể đang được cài đặt trực tiếp trong mã nguồn.

## 2.1. Danh sách Người dùng (Actors)

Hệ thống phân chia quyền theo 2 cấp: cấp **Đội nhóm (Team)** và cấp **Dự án (Project)**.

| Tác nhân | Cấp độ | Vai trò & Quyền hạn chính |
| --- | --- | --- |
| **Khách (Guest)** | Chung | Chỉ xem được giao diện trang giới thiệu hoặc điền link xác nhận tham gia team. |
| **Người dùng chung** | Cá nhân | Quản lý thông tin cá nhân, đổi mật khẩu và **tự cài đặt lịch làm việc cá nhân (WorkSchedule)**. |
| **Chủ sở hữu Team** | Team | Có toàn quyền cao nhất trong một Đội nhóm (Xóa team, đuổi thành viên, trao quyền). |
| **Quản lý Team** | Team | Có quyền duyệt mời thành viên mới và tạo các dự án mới cho team. |
| **Chủ Dự án** | Dự án | Người tạo dự án, có quyền thiết lập chi tiết các Trạng thái (Status) và phân loại riêng cho dự án đó. |
| **Thành viên Dự án** | Dự án | Người trực tiếp làm việc: Tạo công việc, báo cáo giờ làm, cập nhật tiến độ, kéo thả trạng thái. |
| **Người xem (Viewer)** | Dự án | Quyền chỉ xem tiến độ chung, không được phép chỉnh sửa bất cứ dữ liệu nào. |
| **Trợ lý AI (Hệ thống)**| Tác nhân | Chạy quét dữ liệu ngầm định kỳ, phân tích dữ liệu và tự động kích hoạt hệ thống Email nhắc nhở. |

---

## 2.2. Yêu cầu chức năng (Các tính năng đã hoàn thiện)

### 2.2.1. Quản lý Năng suất & Lịch biểu
- **Thiết lập thời gian biểu**: Mỗi thành viên tự điền giờ bắt đầu, giờ kết thúc và đánh dấu ngày nghỉ cố định cho từng thứ trong tuần.
- **Kiểm tra quỹ thời gian**: Hệ thống tự đếm xem từ thời điểm hiện tại đến hạn chót (Due Date), nhân sự còn trống chính xác bao nhiêu giờ làm việc thực tế dựa trên lịch biểu cá nhân đã khai báo.
- **Gộp lịch cá nhân**: Tự động gom nhóm toàn bộ sự kiện và lịch họp từ các team khác nhau để hiển thị thống nhất tại trang Dashboard chung.

### 2.2.2. Vận hành Dự án & Quản trị Giao diện
- **Xem công việc linh hoạt**: Hỗ trợ 2 dạng xem dữ liệu thực tế:
  - **Dạng Bảng (Board view)**: Theo dõi tiến độ thông qua các cột Kanban, hỗ trợ kéo thả trực quan.
  - **Dạng Danh sách (List view)**: Dạng bảng dòng dữ liệu, tối ưu cho việc lọc và sắp xếp khối lượng lớn công việc.
- **Cấu hình Metadata dự án**: Không phụ thuộc khuôn mẫu cứng, cho phép tùy biến chuyên sâu:
  - Tự tạo bộ **Task Status** riêng (đặt tên, chọn mã màu HEX riêng).
  - Tạo bộ **Task Types** riêng (có thể gán icon đại diện như Bug, Feature, Epic...).
  - Thiết lập cấp độ **Ưu tiên (Priority)** và gắn **Nhãn (Tags)** không giới hạn.

### 2.2.3. Quản lý Tác vụ & Ghi nhận nỗ lực (Tasks)
- **Theo dõi thời gian (Effort tracking)**: Hỗ trợ điền số giờ ước lượng ban đầu (`estimated_hours`) và liên tục cập nhật giờ thực tế đã làm (`actual_hours`) để hệ thống đo lường độ trễ.
- **Phân công công việc**: Giao việc cho một hoặc nhiều thành viên cùng thực hiện chung một Task.
- **Đính kèm mô tả**: Soạn thảo nội dung chi tiết yêu cầu bằng văn bản.

### 2.2.4. Hệ thống AI Phân tích & Cảnh báo (AI Core)
- **Báo cáo Phân tích rủi ro (Risk Dashboard)**: Giao diện trực quan hiển thị Biểu đồ Phân phối rủi ro (Risk Matrix) và Đồng hồ đo điểm số nguy cấp của toàn bộ dự án.
- **Tính toán Tín hiệu Rủi ro**: Tự động thu thập và tính toán:
  - Chênh lệch giữa thời gian ước lượng và thời gian làm thực tế.
  - Mật độ đầu việc chạy song song đang dồn lên vai một nhân sự (Congestion).
  - Sai lệch lịch sử: Dựa vào trung bình số giờ ước lượng sai trong quá khứ của người dùng đó để hiệu chuẩn lại.
- **Tổng hợp khuyến nghị**: AI đọc các chỉ số khô khan trên và viết lại thành lời khuyên quản trị ngắn gọn gửi tới quản lý.
- **Cảnh báo Email chủ động (Proactive SMTP Alert)**: Hệ thống tự động gửi email thông báo cho cả người làm và quản lý khi điểm số rủi ro của tác vụ vượt qua ngưỡng 70% (0.70).

---

## 2.3. Yêu cầu phi chức năng (Phi kỹ thuật)

| Yếu tố | Giải pháp thực thi trong mã nguồn |
| --- | --- |
| **An toàn dữ liệu** | Áp dụng cơ chế Xóa mềm (Soft delete) khi xóa dự án/task, đảm bảo không làm gãy liên kết dữ liệu lịch sử của các phân tích AI. |
| **Truy vết hoạt động** | Sử dụng thư viện Opik để ghi lại toàn bộ quá trình gọi và phản hồi của AI, giúp theo dõi lượng token tiêu thụ và dò lỗi hệ thống nhanh. |
| **Tốc độ & Hiệu năng** | Áp dụng Prefetching (Tải trước dữ liệu) kết hợp TanStack Query Cache để đảm bảo khi người dùng bấm chuyển trang, dữ liệu dự án gần như đã có sẵn trên giao diện. |
| **Dự phòng lỗi** | Xây dựng thuật toán dự phòng (Fallback strategy): Nếu kết nối AI gặp sự cố mạng, hệ thống tự động chuyển sang phương án tính toán thủ công bằng Python để đảm bảo chức năng báo cáo không bị gián đoạn. |
