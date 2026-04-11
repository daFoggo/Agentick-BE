# Agentick Backend - Hướng dẫn vận hành

Dự án Backend cho hệ thống Agentick, xây dựng trên nền tảng **FastAPI (Clean Architecture)**, sử dụng **PostgreSQL** và quản lý môi trường bằng **Docker**.

---

## 🚀 Hướng dấn chạy dự án lần đầu (Dành cho người mới)

Chỉ cần làm đúng 3 bước theo thứ tự sau để khởi chạy dự án:

**Bước 1: Cấu hình môi trường (.env)**
Tạo một file có tên là `.env` ở ngay thư mục gốc của project (nơi chứa file `docker-compose.yml`) với các thông số bắt buộc:
```env
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
DATABASE_URL=
SECRET_KEY=
ENV=dev
```
*(Lưu ý: KHÔNG bao giờ commit file này lên Git)*

**Bước 2: Khởi chạy hệ thống bằng Docker**
Build và chạy các dịch vụ (Database & API) bằng lệnh sau:
```bash
docker compose up -d --build
```
*(Chờ khoảng 5-10 giây để cơ sở dữ liệu khởi động hoàn toàn)*

**Bước 3: Khởi tạo các bảng trong Database (Migrations)**
Container đã chạy nhưng database hiện tại vẫn đang trống. Chạy lệnh sau để tự động tạo cấu trúc bảng (như bảng `user`, ...):
```bash
docker exec agentick-be-api alembic upgrade head
```

🎉 **Xong!** Hệ thống API đã sẵn sàng. Truy cập ngay tài liệu API tại: `http://localhost:8000/docs`

---

## 🛠 Các lệnh quản lý nâng cao (Maintenance)

Dưới đây là một số lệnh cần thiết khi phát triển thêm tính năng hoặc fix bug:

| Lệnh | Mô tả |
| :--- | :--- |
| `docker logs -f agentick-be-api` | Xem log đang chạy trực tiếp của Backend (để trace lỗi) |
| `docker compose down -v` | **Hiểm hoạ:** Dừng và xoá sạch tinh hoàn toàn Database đang có, đưa về trạng thái trắng xoá để tạo lại lỗi từ đầu |
| `docker exec agentick-be-api alembic revision --autogenerate -m "tên"` | Tự động tạo bản cập nhật mới (file migration python) mỗi khi sửa file `.py` thuộc Model cấu trúc Database |
| `docker exec agentick-be-api alembic upgrade head` | Áp dụng các thay đổi trong file migration vào trong Database thật |

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
