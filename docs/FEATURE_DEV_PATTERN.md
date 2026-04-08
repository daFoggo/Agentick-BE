# Hướng dẫn Phát triển tính năng & Quy ước Code (Clean Architecture)

Tài liệu này dùng để định hướng cách xây dựng một tính năng mới (ví dụ: Quản lý Project, Task) sao cho đúng chuẩn kiến trúc của dự án.

---

## 1. Quy trình phát triển một tính năng (8 bước chuẩn)

Khi thêm một thực thể (Entity) mới, hãy follow theo thứ tự sau để tránh sai sót:

1. **Model**: Định nghĩa bảng tại `app/model/`. Lưu ý kế thừa `BaseModel`.
2. **Schema**: Tạo Input/Output/Search schema tại `app/schema/`. 
   - Sử dụng `EmailStr`, `Field` để validate.
   - Luôn định nghĩa Search schema với hậu tố `__eq`, `__ilike`...
3. **Repository**: Tạo file repository tại `app/repository/`. Kế thừa `BaseRepository` để có sẵn các hàm CRUD.
4. **Service**: Viết logic nghiệp vụ tại `app/services/`.
   - Đây là nơi xử lý logic "thông minh", kiểm tra điều kiện, tính toán.
5. **Endpoint**: Khai báo Route tại `app/api/v1/endpoints/`.
   - **Bắt buộc**: Bọc kết quả trả về trong `ResponseSchema`.
6. **Container**: Đăng ký Repository và Service vào DI Container tại `app/core/container.py`.
7. **Migration**: Chạy Alembic để cập nhật Database:
   - `docker exec agentick-be-api alembic revision --autogenerate -m "Add feature X"`
   - `docker exec agentick-be-api alembic upgrade head`
8. **Test**: Viết Integration Test cho Endpoint tại `tests/integration_tests/`.

---

## 2. Quy ước Code (Coding Convention)

### 2.1. Quy chuẩn phản hồi (API Response)
Tất cả các Endpoint phải trả về dữ liệu theo cấu trúc:
```python
return ResponseSchema(
    success=True,
    message="Thông báo",
    data=result
)
```

### 2.2. Xử lý lỗi (Error Handling)
Sử dụng các Exception đã định nghĩa sẵn tại `app/core/exceptions.py`:
- `AuthError` -> **401 Unauthorized** (Dùng cho lỗi đăng nhập, token).
- `DuplicatedError` -> **400 Bad Request** (Dùng cho lỗi trùng lặp dữ liệu).
- `NotFoundError` -> **404 Not Found** (Dùng khi không tìm thấy ID).
- `ValidationError` -> **422 Unprocessable Entity** (Dùng khi dữ liệu đầu vào sai format).

### 2.3. Quy tắc đặt tên
- **File**: `snake_case.py`
- **Class**: `PascalCase` (Ví dụ: `UserService`)
- **Function/Variable**: `snake_case`
- **Search field**: `<field>__<operator>` (Ví dụ: `email__eq`, `name__ilike`)
- **API Path**: `kebab-case` (Ví dụ: `/api/v1/auth/sign-in`)

---

## 3. Checklist trước khi Merge Code

- [ ] Đã tách rõ trách nhiệm giữa Endpoint (HTTP) - Service (Logic) - Repository (DB) chưa?
- [ ] Dữ liệu trả về đã được bọc trong `ResponseSchema` chưa?
- [ ] Có bị lộ thông tin nhạy cảm (Password, Secret) trong Response không?
- [ ] Đã chạy Migration để cập nhật DB chưa?
- [ ] Đã viết ít nhất 1 Happy-path Test chưa?
- [ ] Mã lỗi trả về có đúng chuẩn (401 cho Auth, 404 cho không tìm thấy) chưa?

---
*Tuân thủ đúng các quy tắc trên sẽ giúp dự án luôn sạch sẽ, dễ bảo trì và mở rộng.*
