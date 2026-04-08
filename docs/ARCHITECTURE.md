# Tài liệu Kiến trúc Dự án (Clean Architecture)

Tài liệu này giải thích cách tổ chức mã nguồn của Agentick Backend theo phong cách **Clean Architecture**. Để dễ hình dung, chúng ta hãy coi toàn bộ hệ thống này như một **nhà hàng**:

- **Khách gọi món** = Client gửi HTTP request.
- **Lễ tân** = Router (Điều hướng khách).
- **Người nhận order** = Endpoint (Kiểm tra menu, ghi yêu cầu).
- **Bếp trưởng** = Service (Thực hiện logic nấu nướng, công thức nghiệp vụ).
- **Kho nguyên liệu** = Repository (Lấy dữ liệu thô).
- **Sổ cái / Tủ hồ sơ** = Database (Nơi lưu trữ bền vững).

> **Nguyên tắc cốt lõi:** Request đi vào Router -> Endpoint -> Service -> Repository -> Database.

---

## 1. Các lớp chính trong Project

- **`app/main.py`**: Điểm khởi đầu của ứng dụng, nơi cấu hình FastAPI, Middleware và các Router.
- **`app/core/`**: Trái tim của hệ thống bao gồm: Cấu hình (Config), Kết nối DB, Bảo mật (Security), Exception handling.
- **`app/api/`**: Tầng giao tiếp với bên ngoài. Chỉ lo việc nhận Request và trả về Response.
- **`app/services/`**: Tầng chứa Logic nghiệp vụ. Đây là nơi "thông minh" nhất của dự án.
- **`app/repository/`**: Tầng truy xuất dữ liệu. Không quan tâm logic là gì, chỉ quan tâm lấy dữ liệu từ DB như thế nào.
- **`app/model/`**: Định nghĩa các bảng Database (SQLAlchemy).
- **`app/schema/`**: Định nghĩa kiểu dữ liệu (Pydantic) để validate dữ liệu đầu vào và đầu ra.

---

## 2. Luồng chạy của một Request (Ví dụ: Đăng nhập)

1. **Client** gọi `POST /api/v1/auth/sign-in`.
2. **FastAPI** tìm Router phù hợp trong `app/api/v1/routes.py`.
3. **Endpoint** (`auth.py`) nhận dữ liệu, kiểm tra tính hợp lệ bằng `SignInSchema`.
4. **Service** (`AuthService`) thực hiện kiểm tra:
   - Gọi **Repository** để lấy User theo email.
   - So khớp mật khẩu đã băm (Hashed Password).
   - Nếu đúng, gọi `create_access_token` để tạo JWT.
5. **Endpoint** nhận kết quả và bọc vào `ResponseSchema` để trả về cho Client.

---

## 3. Lý do sử dụng kiến trúc này

1. **Dễ bảo trì**: Bạn muốn đổi Database từ Postgres sang MySQL? Chỉ cần sửa lớp Repository, các lớp khác không bị ảnh hưởng.
2. **Dễ kiểm thử (Testing)**: Bạn có thể viết Unit Test cho Service mà không cần bật Database thật lên (bằng cách dùng Mock Repository).
3. **Tính mở rộng**: Khi cần ra mắt API v2, bạn chỉ cần tạo thêm folder `api/v2` mà không làm hỏng logic của v1.

---

## 4. Cách thêm một tính năng mới (Thực hiện theo các bước)

1. **Model**: Định nghĩa bảng trong `app/model/`.
2. **Schema**: Định nghĩa dữ liệu vào/ra trong `app/schema/`.
3. **Repository**: Viết các hàm CRUD cơ bản trong `app/repository/`.
4. **Service**: Viết logic nghiệp vụ trong `app/services/`.
5. **Endpoint**: Tạo các đường dẫn API trong `app/api/v1/endpoints/`.
6. **Route**: Đăng ký endpoint mới vào `app/api/v1/routes.py`.
7. **Migration**: Chạy lệnh Alembic để cập nhật Database.

---
*Tài liệu này giúp đảm bảo mọi thành viên trong dự án đều code theo một hướng thống nhất.*
