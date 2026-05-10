# 7. Chi tiết Quy tắc & Luồng Nghiệp vụ (Detailed Business Logic)

Tài liệu này cung cấp các quy tắc vận hành cụ thể của hệ thống, kịch bản xử lý lỗi và các bước thực hiện nghiệp vụ chi tiết. Dành cho BA và Đội ngũ kiểm thử (QC/QA).

---

## 7.1. Các Quy tắc Nghiệp vụ Cứng (Business Rules)

Dưới đây là các ràng buộc bắt buộc hệ thống phải kiểm tra trước khi thực hiện bất kỳ thao tác nào:

### Về Quyền Hạn & Bảo mật
1. **Tạo/Xóa Dự án**: Chỉ người dùng có vai trò là `Owner` (Chủ) hoặc `Manager` (Quản lý) trực thuộc Đội nhóm (Team) mới có quyền tạo hoặc xóa Dự án. Mọi thành viên thường (`Member`) đều bị chặn.
2. **Truy cập Thông tin**: Một thành viên dù thuộc cùng một Team NHƯNG nếu không nằm trong danh sách `ProjectMember` của một Dự án cụ thể, thì TUYỆT ĐỐI không được phép xem, đọc hay sửa dữ liệu của dự án đó.
3. **Tạo Công việc (Task)**: Chỉ những người đã được Add vào Dự án mới được phép tạo Task mới cho dự án đó.

### Về Vòng đời Dữ liệu
4. **Xóa Công việc**: Không bao giờ xóa vĩnh viễn Task khỏi Database để bảo vệ lịch sử phân tích AI. Hệ thống chỉ đánh dấu ẩn (`is_deleted = true`).
5. **Lịch biểu (Calendar)**: Khi một Task bị Xóa (ẩn), hệ thống BUỘC PHẢI XÓA CỨNG (Xóa hoàn toàn) toàn bộ các Sự kiện (`Event`) đi kèm trên Lịch biểu của nhân viên để trả lại quỹ thời gian trống.

---

## 7.2. Các Kịch bản Xử lý Lỗi (Error Cases Mapping)

Hệ thống thiết kế luồng phản hồi chuẩn hóa cho các tình huống nghiệp vụ đi sai hướng:

| Loại lỗi | Mã lỗi (HTTP) | Tình huống kích hoạt thực tế | Phản hồi từ Hệ thống |
| --- | --- | --- | --- |
| **Auth Error** | `401 Unauthorized` | Token JWT hết hạn sau 30 phút, hoặc chữ ký số không hợp lệ. | Yêu cầu người dùng Log out và đăng nhập lại. |
| **Permission Denied** | `403 Forbidden` | Nhân viên thường cố tình gọi API xóa dự án, hoặc vào link dự án của team khác. | Báo lỗi "Bạn không có quyền thực hiện hành động này". |
| **Resource Missing** | `404 Not Found` | Truy cập vào một Task hoặc Dự án đã bị xóa (`is_deleted=true`). | Báo lỗi "Tài nguyên không tồn tại". |
| **Data Integrity** | `409 Conflict` | Cố tình đăng ký tài khoản bằng một Email đã được người khác sử dụng rồi. | Báo lỗi "Email này đã tồn tại trên hệ thống". |
| **Model Downtime** | `200 (Fallback)` | Khi API AI của bên thứ 3 (OpenRouter) bị sập hoặc quá tải request. | Hệ thống tự kích hoạt mã lệnh Python tính tay giá trị trung bình để không làm treo ứng dụng. |

---

## 7.3. Luồng Vận hành các Tính năng Phức tạp (Complex Workflows)

Mô tả cụ thể các bước mà hệ thống tự động nhảy qua khi người dùng thực hiện lệnh.

### 7.3.1. Quy trình: Đăng ký & Kích hoạt Tự động (Atomic Registration)
Khi khách hàng bấm nút Đăng ký, hệ thống kích hoạt một chuỗi dây chuyền đồng bộ 100%:
* **Bước 1**: Mã hóa mật khẩu bằng thuật toán Bcrypt và lưu User mới.
* **Bước 2**: Tự động sinh ra 1 Team mang tên người dùng để họ có không gian làm việc ngay lập tức.
* **Bước 3**: Tiếp tục sinh ra 1 Dự án mặc định nằm gọn trong Team đó.
* **Bước 4**: Kích hoạt bộ gieo hạt (Seed), tự chèn 6 Trạng thái (To do, Done...) vào bảng dữ liệu Dự án vừa sinh.
* **Bước 5**: Tự sinh 2 bộ Lịch (Cá nhân & Nhóm) và chèn sẵn khung giờ làm 8 tiếng/ngày cho cả tuần.
* **Bước 6**: Lưu tất cả xuống CSDL cùng 1 lúc. Nếu bất kỳ bước nào trong 5 bước trên bị lỗi, hệ thống TỰ HỦY TOÀN BỘ (Rollback), không lưu rác vào DB.

### 7.3.2. Quy trình: Morning Scan (Quét Rủi ro Chủ động)
Nhiệm vụ: Tự động nhận diện xem task nào có nguy cơ bị trễ tiến độ vào 9:00 AM mỗi ngày (giờ địa phương của từng dự án).
*   **Trigger**: Scheduler (Tự động chạy ngầm 24/7 mỗi giờ) HOẶC Force-API.
*   **Bước 1: Lọc Khung giờ**: Hệ thống gom nhóm toàn bộ dự án, tính toán timezone và lọc ra các task đang thuộc múi giờ 9:00 sáng.
*   **Bước 2: Chạy Song song**: Kích hoạt Async Worker xử lý hàng loạt đồng thời.
*   **Bước 3: Phân tích Logic**: AI đọc thô: Giờ dự kiến, Tiến độ % thực tế, các Blockers hiện tại.
*   **Bước 4: Phản ứng Khẩn**: Nếu điểm Rủi ro AI chấm `>= 0.8` (Mức High/Critical), hệ thống lập tức gửi Email cảnh báo đỏ trực tiếp đến nhân viên và người giao việc để can thiệp nóng.

### 7.3.3. Quy trình: Agent Outreach (Truy thu & Nhắc nhở Dữ liệu)
Đóng vai trò "Thư ký ảo" đi nhắc Developer lười cập nhật số liệu.
*   **Điều kiện Kích hoạt**: Chỉ chạy cho Task active. Có 2 diện vi phạm:
    *   **Data Gap**: Thiếu trường Estimated Hours (Trường bắt buộc để AI đo lường).
    *   **Stale**: Task còn < 3 ngày đến hạn nhưng 24h qua không hề có bất kỳ thao tác cập nhật hay báo tiến độ nào.
*   **Luồng thực thi**: 
    *   Gom nhóm nhân viên vi phạm vào Batch Job.
    *   AI soạn thư tự động: Sử dụng giọng điệu lịch sự nhưng mang tính khẩn cấp, lồng ghép câu hỏi còn thiếu cho từng context công việc riêng biệt.
    *   Gửi thư & Chặn Spam: Cơ chế khóa Anti-Spam 24h tuyệt đối không gửi thư lần 2 cho cùng 1 vi phạm trong ngày.

### 7.3.4. Quy trình: Evening Summary (Báo cáo Tổng hợp Sếp)
Nén toàn bộ diễn biến trong ngày thành 1 bản báo cáo gọn gàng nhất cho Team Lead vào 5:30 PM cuối giờ chiều.
*   **Lọc dữ liệu**: Không báo cáo lan man. Chỉ nhặt các Risk Snapshot có điểm `>= 0.5` (Những Task đang có vấn đề thực sự) sinh ra trong hôm nay.
*   **Email Đích**: Tự động lookup Email thật của Chủ sở hữu Dự án (Project Owner) thay vì cấu hình cứng.
*   **Output**: Gửi một Dashboard HTML tổng thể thể hiện điểm nóng của toàn bộ dự án. Giúp quản lý không cần mở app cũng nắm bắt được tình trạng "Sức khỏe" đội ngũ trước khi tan làm.
