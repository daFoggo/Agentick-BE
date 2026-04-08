# Agentick Backend - Hướng dẫn vận hành

Dự án Backend cho hệ thống Agentick, xây dựng trên nền tảng **FastAPI (Clean Architecture)**, sử dụng **PostgreSQL** và quản lý môi trường bằng **Docker**.

---

## 🚀 Các lệnh thường dùng (Quick Start)

### 1. Quản lý Container (Docker)
| Lệnh | Mô tả |
| :--- | :--- |
| `docker compose up --build` | Xây dựng và khởi chạy hệ thống (xem log trực tiếp) |
| `docker compose up -d` | Chạy hệ thống ở chế độ chạy ngầm |
| `docker compose down` | Dừng và xóa các container |
| `docker compose down -v` | **Cẩn thận:** Dừng và xóa sạch toàn bộ dữ liệu Database |
| `docker logs -f agentick-be-api` | Xem log trực tiếp của Backend |

### 2. Quản lý Database (Alembic Migrations)
Bạn cần chạy các lệnh này mỗi khi thay đổi cấu trúc Database (thêm trường, thêm bảng). Chạy trực tiếp qua container đang hoạt động:

| Lệnh | Mô tả |
| :--- | :--- |
| `docker exec agentick-be-api alembic revision --autogenerate -m "Mô tả"` | Tự động tạo bản cập nhật mới (migration script) |
| `docker exec agentick-be-api alembic upgrade head` | Áp dụng tất cả các thay đổi vào Database thật |
| `docker exec agentick-be-api alembic history` | Xem lịch sử các bản migration |

---

## 🛠 Cấu hình Môi trường (.env)

File `.env` là nơi chứa các bí mật và cấu hình. **KHÔNG bao giờ commit file này lên Git.**

Các biến quan trọng:
- `SECRET_KEY`: Chìa khóa để mã hóa JWT Token. (Đã bổ sung chuỗi bảo mật).
- `DATABASE_URL`: Đường dẫn kết nối DB (Đã được cấu hình chuẩn cho Docker).
- `POSTGRES_PASSWORD`: Mật khẩu của Database PostgreSQL.

---

## 📐 Kiến trúc Phản hồi (Standard Response Format)

Dự án đã được chuẩn hóa format trả về cho tất cả API theo chuẩn RESTful:

```json
{
  "success": true,
  "message": "Thông báo thành công/thất bại",
  "data": { ... dữ liệu thực tế ... }
}
```

- **Mã lỗi 401 (Unauthorized)**: Trả về khi sai mật khẩu, sai email hoặc Token hết hạn.
- **Mã lỗi 422 (Unprocessable Entity)**: Trả về khi dữ liệu đầu vào không hợp lệ (ví dụ: mật khẩu ngắn hơn 6 ký tự).

---

## 📁 Cấu trúc Thư mục

- `app/api/v1/endpoints/`: Nơi định nghĩa các Route (URL).
- `app/services/`: Nơi xử lý logic nghiệp vụ chính (Business Logic).
- `app/repository/`: Nơi tương tác trực tiếp với Database (SQLAlchemy).
- `app/model/`: Nơi định nghĩa cấu trúc bảng Database.
- `app/schema/`: Nơi định nghĩa kiểu dữ liệu Input/Output (Pydantic).
- `migrations/`: Lưu trữ các bản ghi thay đổi cấu trúc DB.

---

## 🛡 Bảo mật & Quy tắc Code

1. **Password**: Độ dài tối thiểu **6 ký tự**. Được mã hóa bằng Argon2/Bcrypt trước khi lưu.
2. **JWT**: Sử dụng Bearer Token để xác thực người dùng.
3. **CORS**: Hiện đang cho phép mọi nguồn (`*`) để thuận tiện phát triển. Cần giới hạn lại khi triển khai thực tế.
4. **Validation**: Luôn sử dụng Pydantic Schema để kiểm tra dữ liệu từ Client gửi lên.

---

## 🔗 Tài liệu API (Interactive Docs)
Sau khi khởi chạy Docker thành công, bạn có thể trSau khi chạy, API sẽ có sẵn tại: `http://localhost:8000/api/v1/ping`
Tài liệu API (Swagger UI): `http://localhost:8000/docs`

---

## 📘 Tài liệu Kỹ thuật & Kiến trúc
Để hiểu sâu hơn về cách tổ chức Code và quy trình phát triển, hãy đọc các tài liệu sau:
- [Kiến trúc dự án (Clean Architecture)](./docs/ARCHITECTURE.md) - Giải thích về các tầng Service, Repository, v.v.
- [Quy trình phát triển tính năng mới](./docs/FEATURE_DEV_PATTERN.md)

---
