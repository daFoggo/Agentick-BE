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

### 7.3.2. Quy trình: "Bộ não" Phân tích Rủi ro (AI Reasoning Loop)
Đây là luồng chạy ngầm định kỳ hoặc khi người dùng bấm nút yêu cầu AI nhận định:
* **Nhận dữ liệu thô**: Đọc tổng số giờ làm của Task hiện tại.
* **Chạy vòng lặp Python**: Duyệt lịch làm việc từ hôm nay đến ngày Deadline, đếm chính xác số giờ làm thực tế (trừ ngày nghỉ) để tính toán quỹ thời gian còn lại.
* **Tính độ nhiễu**: Đếm xem nhân viên này đang ôm bao nhiêu việc khác cùng lúc (Congestion).
* **Suy luận LLM**: Chuyển số liệu đã tính đẹp đẽ cho AI. AI chỉ đóng vai trò "Bình luận viên" đưa ra điểm rủi ro và lời khuyên.
* **Bắn Cảnh báo**: Nếu điểm Rủi ro vượt quá ngưỡng 0.7, hệ thống tự chui vào hộp thư, soạn Email và gửi thẳng cho Người giao việc ngay lập tức để can thiệp kịp thời.
