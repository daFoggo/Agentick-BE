# Getting Started (Hướng dẫn bắt đầu)

Dự án này sử dụng **Python 3.12**, **uv** để quản lý package và **Docker** để vận hành môi trường.

## 1. Sử dụng Docker (Khuyên dùng)

Đây là cách nhanh nhất để chạy dự án với đầy đủ database.

```powershell
# 1. Khởi chạy dự án (Kèm build image lần đầu)
docker compose up --build

# 2. Khởi chạy ở chế độ chạy ngầm (nếu muốn)
docker compose up -d

# 3. Dừng và xóa container/network
docker compose down

# 4. Dừng và xóa cả dữ liệu database (để reset trắng)
docker compose down -v
```

Sau khi chạy, API sẽ có sẵn tại: `http://localhost:8000/api/ping`
Tài liệu API (Swagger UI): `http://localhost:8000/docs`

## 2. Chạy Local (Không dùng Docker)

Nếu bạn muốn chạy trực tiếp trên máy để debug sâu:

**Yêu cầu:** Cài đặt [uv](https://github.com/astral-sh/uv).

```powershell
# 1. Cài đặt dependencies
uv sync

# 2. Setup database (Yêu cầu bạn đã có Postgres đang chạy)
# Cập nhật thông tin trong file .env

# 3. Chạy Server với tính năng Hot Reload
uv run uvicorn app.main:app --reload
```

## 3. Quản lý Database (Alembic)

Dự án sử dụng Alembic để quản lý phiên bản database.

```powershell
# Tạo một bản migration mới sau khi sửa Model
docker compose exec api uv run alembic revision --autogenerate -m "Mô tả thay đổi"

# Cập nhật database lên phiên bản mới nhất
docker compose exec api uv run alembic upgrade head
```

---



Tài liệu này giải thích dự án theo kiểu rất dễ đọc: từ ngoài vào trong, từ request đi đến database rồi quay ngược lại response. Nếu bạn mới học backend, cứ coi toàn bộ hệ thống như một nhà hàng:

- Khách gọi món = client gửi HTTP request.
- Lễ tân = router.
- Người nhận order = endpoint.
- Bếp trưởng = service.
- Kho nguyên liệu = repository.
- Sổ cái / tủ hồ sơ = database.

Nếu chỉ nhớ một câu, hãy nhớ câu này: **request đi vào router, qua endpoint, sang service, rồi repository mới chạm database**.

## 1. Bức tranh tổng quan

Đây là một backend FastAPI theo hướng clean architecture. Mục tiêu của nó không phải là viết càng ít file càng tốt, mà là chia trách nhiệm rõ ràng để:

- Dễ đọc.
- Dễ test.
- Dễ thay đổi từng phần mà không làm hỏng toàn bộ hệ thống.
- Có thể mở rộng theo nhiều version API.

Các lớp chính trong project là:

- `app/main.py`: nơi tạo app FastAPI.
- `app/core/`: cấu hình, DB, security, dependency injection, middleware, exceptions.
- `app/api/`: nơi định nghĩa endpoint HTTP.
- `app/services/`: logic nghiệp vụ.
- `app/repository/`: truy cập dữ liệu.
- `app/model/`: model ORM ánh xạ bảng database.
- `app/schema/`: schema validate input/output.
- `app/util/`: hàm tiện ích.
- `tests/`: test fixture, test data, integration/unit tests.

## 2. Luồng chạy của một request

Một request đi theo chuỗi này:

1. Client gọi URL, ví dụ `/api/v1/user`.
2. FastAPI tìm router phù hợp trong `app/api/v1/routes.py`.
3. Router chuyển request cho endpoint cụ thể, ví dụ `app/api/v1/endpoints/user.py`.
4. Endpoint nhận dữ liệu đã được validate bằng schema.
5. Endpoint gọi service, ví dụ `UserService` hoặc `AuthService`.
6. Service gọi repository để đọc/ghi dữ liệu.
7. Repository mở session DB, chạy query, trả kết quả.
8. Response được serialize theo `response_model` rồi trả lại client.

Điểm quan trọng: endpoint không nên tự viết query SQL, service không nên lo chi tiết HTTP, repository không nên lo business rule. Mỗi lớp làm đúng việc của nó.

## 3. Điểm vào của ứng dụng

File khởi động chính là [app/main.py](../app/main.py).

Trong file này có class `AppCreator`, được bọc bằng singleton để chỉ khởi tạo một lần. Nó làm 4 việc chính:

- Tạo `FastAPI` app.
- Tạo container dependency injection.
- Lấy database object từ container.
- Gắn router và middleware vào app.

Ngoài ra còn có route gốc `/` trả về chuỗi `service is working` để kiểm tra service còn sống hay không.

## 4. Cấu hình môi trường

File quan trọng là [app/core/config.py](../app/core/config.py).

Ở đây project đọc biến môi trường như:

- `ENV`
- `DB`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `SECRET_KEY`

Từ đó nó ghép ra `DATABASE_URI` và các đường dẫn API như:

- `/api`
- `/api/v1`
- `/api/v2`

Tóm lại: muốn đổi database hay môi trường chạy, bạn không sửa logic app, bạn đổi biến môi trường.

## 5. Dependency Injection là gì

Project này dùng `dependency-injector`. Bạn có thể hiểu đơn giản như sau:

- Không tự `new` service/repository khắp nơi.
- Thay vào đó, container sẽ tạo và cung cấp chúng khi endpoint cần.

File chính là [app/core/container.py](../app/core/container.py).

Trong container có:

- `db`: singleton Database.
- `post_repository`, `tag_repository`, `user_repository`: factory repository.
- `auth_service`, `post_service`, `tag_service`, `user_service`: factory service.

Vì sao làm vậy?

- Dễ thay dependency khi test.
- Tách cấu trúc rõ ràng.
- Không phụ thuộc cứng giữa các lớp.

## 6. Database và session

File chính là [app/core/database.py](../app/core/database.py).

Project dùng SQLModel cho model ORM, nhưng cách vận hành session vẫn là session SQLAlchemy quen thuộc:

- Mỗi request/service sẽ dùng session từ `Database.session()`.
- Nếu có lỗi thì rollback.
- Cuối cùng luôn close session.

Điều này rất quan trọng vì DB session giống như một cuộc gọi đang mở. Mở xong phải đóng, không thì tài nguyên bị giữ lại và app sẽ chậm hoặc lỗi.

### Model database

Các model nằm trong `app/model/`:

- [app/model/user.py](../app/model/user.py)
- [app/model/post.py](../app/model/post.py)
- [app/model/tag.py](../app/model/tag.py)
- [app/model/post_tag.py](../app/model/post_tag.py)

Ý nghĩa của chúng:

- `User`: người dùng.
- `Post`: bài viết.
- `Tag`: nhãn/chủ đề.
- `PostTag`: bảng nối quan hệ nhiều-nhiều giữa post và tag.

`BaseModel` trong [app/model/base_model.py](../app/model/base_model.py) cung cấp các cột chung:

- `id`
- `created_at`
- `updated_at`

### Quan hệ dữ liệu

- Một user có thể có nhiều post.
- Một post có thể có nhiều tag.
- Một tag có thể gắn cho nhiều post.

Nếu bạn mới học backend, hãy coi đây là 3 thực thể chính và 1 bảng nối.

## 7. Schema là gì

Schema nằm trong `app/schema/` và dùng để validate dữ liệu vào/ra.

Nói rất ngắn gọn:

- `model` = cấu trúc trong database.
- `schema` = cấu trúc dữ liệu mà API nhận hoặc trả.

Tách như vậy để tránh lộ toàn bộ database model ra API một cách vô tội vạ.

### Các schema quan trọng

- [app/schema/auth_schema.py](../app/schema/auth_schema.py): đăng nhập, đăng ký, token payload.
- [app/schema/user_schema.py](../app/schema/user_schema.py): user, tìm kiếm user, tạo/cập nhật user.
- [app/schema/base_schema.py](../app/schema/base_schema.py): các phần chung như phân trang, sắp xếp, `Blank`.

### Một điểm đáng chú ý

Schema tìm kiếm của project dùng kiểu lọc khá linh hoạt, ví dụ `email__eq`. Nghĩa là nó giống tư duy query builder hơn là chỉ nhận JSON đơn giản.

## 8. Repository làm gì

Repository là tầng chạm vào database thật.

File nền là [app/repository/base_repository.py](../app/repository/base_repository.py).

Nó có các thao tác cơ bản:

- Đọc danh sách theo điều kiện.
- Đọc một bản ghi theo id.
- Tạo mới.
- Cập nhật.
- Xóa.

Nó cũng xử lý:

- phân trang,
- sắp xếp,
- lọc động từ schema,
- eager loading khi cần.

Ý tưởng rất đơn giản: service không cần biết câu query cụ thể, repository lo phần đó.

## 9. Service làm gì

Service nằm trong `app/services/` và là nơi chứa logic nghiệp vụ.

File nền là [app/services/base_service.py](../app/services/base_service.py).

Base service chỉ là lớp bọc mỏng quanh repository, cung cấp các hàm như:

- `get_list`
- `get_by_id`
- `add`
- `patch`
- `remove_by_id`

Các service cụ thể như `AuthService`, `UserService`, `PostService`, `TagService` sẽ thêm nghiệp vụ riêng.

Bạn có thể hiểu service là nơi trả lời câu hỏi:

- “Được phép làm gì?”
- “Làm theo thứ tự nào?”
- “Có cần kiểm tra gì trước khi ghi DB không?”

## 10. API layer

API nằm trong `app/api/` và được chia version.

### Version 1

Router gốc của v1 là [app/api/v1/routes.py](../app/api/v1/routes.py).

Nó gộp các router:

- auth
- post
- tag
- user

Các endpoint cụ thể nằm trong `app/api/v1/endpoints/`.

Ví dụ:

- [app/api/v1/endpoints/auth.py](../app/api/v1/endpoints/auth.py)
- [app/api/v1/endpoints/user.py](../app/api/v1/endpoints/user.py)

### Version 2

Router v2 hiện mới có auth ở [app/api/v2/routes.py](../app/api/v2/routes.py).

Điều này cho thấy kiến trúc đã chuẩn bị sẵn cho việc tách API đời mới mà không phá API cũ.

## 11. Auth hoạt động thế nào

Auth là phần dễ làm người mới rối, nên tách ra đọc từng bước.

### Sign up

Endpoint `POST /api/v1/auth/sign-up` nhận dữ liệu đăng ký, gọi `AuthService`, rồi tạo user mới.

### Sign in

Endpoint `POST /api/v1/auth/sign-in` nhận email và password.

Luồng cơ bản là:

- Lấy user theo email.
- So password bằng hàm hash.
- Nếu đúng thì tạo JWT access token.
- Trả về token + thông tin user.

### Bảo vệ route

File lõi là [app/core/security.py](../app/core/security.py) và [app/core/dependencies.py](../app/core/dependencies.py).

Token được đọc bằng `JWTBearer`, sau đó `get_current_user` giải mã token và lấy user từ DB.

Có 3 mức thường gặp:

- `get_current_user`: chỉ cần đăng nhập hợp lệ.
- `get_current_active_user`: user phải active.
- `get_current_super_user`: user phải là admin/superuser.

### Route cần quyền cao hơn

Ví dụ user endpoints trong [app/api/v1/endpoints/user.py](../app/api/v1/endpoints/user.py) dùng `JWTBearer()` và `get_current_super_user` để khóa quyền.

Nói dễ hiểu: không phải ai đăng nhập cũng được sửa/xóa user.

## 12. Middleware và decorator inject

File quan trọng là [app/core/middleware.py](../app/core/middleware.py).

Project có một decorator `@inject` để làm 2 việc:

- Kích hoạt dependency injection của `dependency-injector`.
- Đóng session của service sau khi xử lý xong.

Nếu không đóng session, request tiếp theo có thể bị giữ tài nguyên không cần thiết.

Đây là một chi tiết nhỏ nhưng rất quan trọng cho hệ thống chạy lâu dài.

## 13. Luồng cụ thể: đăng nhập người dùng

Đây là ví dụ thực tế nhất để người mới dễ hình dung.

1. Client gọi `POST /api/v1/auth/sign-in`.
2. FastAPI đọc body vào schema `SignIn`.
3. Endpoint gọi `AuthService.sign_in()`.
4. Service kiểm tra user và password.
5. Nếu hợp lệ, service tạo JWT bằng `create_access_token()`.
6. Response trả về `SignInResponse` gồm:
   - `access_token`
   - `expiration`
   - `user_info`

Ở đây schema, service, security và DB đều tham gia, nhưng mỗi phần chỉ làm đúng nhiệm vụ của mình.

## 14. Luồng cụ thể: lấy danh sách user

Ví dụ `GET /api/v1/user`.

1. Request vào router v1.
2. Route user yêu cầu Bearer token.
3. `get_current_super_user` xác minh quyền admin.
4. `UserService.get_list()` được gọi.
5. `UserRepository.read_by_options()` tạo query theo filter, paging, ordering.
6. Kết quả trả về gồm danh sách `founds` và `search_options`.

Đây là mẫu rất điển hình của clean architecture: HTTP, auth, nghiệp vụ, query, response đều tách riêng.

## 15. Query và phân trang

Project có cơ chế tìm kiếm linh hoạt qua schema `FindBase` và các schema con.

Các trường quen thuộc là:

- `ordering`
- `page`
- `page_size`

Ngoài ra còn có các trường filter đặc thù như `email__eq`.

Ý nghĩa:

- `__eq` = bằng.
- Sau này có thể mở rộng thêm các kiểu khác nếu query builder hỗ trợ.

Nếu bạn mới học backend, hãy hiểu đơn giản: API không chỉ nhận dữ liệu tạo mới, mà còn nhận bộ lọc để tìm kiếm theo điều kiện.

## 16. Test được tổ chức ra sao

Test nằm trong `tests/`.

File setup chính là [tests/conftest.py](../tests/conftest.py).

Điểm đáng chú ý:

- `ENV` được ép thành `test`.
- Database test được reset trước mỗi fixture `client`.
- Dữ liệu mẫu được nạp từ `tests/test_data/users.json` và `tests/test_data/posts.json`.

Có 2 nhóm test chính:

- `tests/integration_tests/`: test luồng API gần giống thực tế.
- `tests/unit_tests/`: test phần cấu hình, container, fixture.

### Vì sao test kiểu này tốt?

Vì bạn không chỉ test một hàm rời rạc. Bạn test cả đường đi của request thật từ API xuống DB, nên dễ bắt lỗi tích hợp hơn.

## 17. Các điểm cần nhớ cho người mới

- Router chỉ biết đường đi của request.
- Endpoint chỉ nhận/trả dữ liệu HTTP.
- Service chứa luật nghiệp vụ.
- Repository chạm DB.
- Schema dùng để validate dữ liệu.
- Model là hình ảnh database.
- Container tự cấp dependency để code bớt dính chùm.
- JWT dùng để biết ai đang gọi API.
- Middleware/decorator ở đây giúp quản lý session sau khi xử lý xong.

Nếu bạn nhớ được 8 dòng này, bạn đã hiểu 80% kiến trúc của repo.

## 18. Nếu muốn thêm một tính năng mới thì làm thế nào

Ví dụ bạn muốn thêm một entity mới, chẳng hạn `Comment`.

Thường bạn sẽ đi theo thứ tự này:

1. Tạo model trong `app/model/`.
2. Tạo schema trong `app/schema/`.
3. Tạo repository trong `app/repository/`.
4. Tạo service trong `app/services/`.
5. Đăng ký dependency trong [app/core/container.py](../app/core/container.py).
6. Tạo endpoint trong `app/api/v1/endpoints/`.
7. Gắn router vào [app/api/v1/routes.py](../app/api/v1/routes.py).
8. Nếu cần, thêm migration bằng Alembic.
9. Viết test trong `tests/`.

Đây là lý do clean architecture hữu ích: thêm tính năng không phải sửa lung tung toàn project.

## 19. Database migration

Repo có `alembic.ini` và thư mục `migrations/`.

Quy trình chuẩn là:

- sửa model trong `app/model/`.
- tạo migration mới.
- xem file migration trong `migrations/versions/`.
- áp dụng migration lên database.

README gốc cũng có các lệnh như `alembic upgrade head` và `alembic revision --autogenerate`.

Nói ngắn gọn: model là ý tưởng, migration là cách biến ý tưởng đó thành schema thật trong DB.

## 20. Những lưu ý thực tế

- `BACKEND_CORS_ORIGINS` đang là `[*]`, thuận tiện khi dev nhưng không nên giữ nguyên kiểu này cho production.
- `SECRET_KEY` phải được cấu hình rõ ràng, không nên để rỗng.
- API v2 mới ở mức khởi đầu, hiện chỉ có auth.
- Project ưu tiên tách lớp rõ ràng, nên sẽ có nhiều file hơn kiểu CRUD tối giản, nhưng đổi lại dễ bảo trì hơn.

## 21. Tóm tắt siêu ngắn

Nếu bạn chỉ có 30 giây, hãy nhớ:

- `app/main.py` tạo app.
- `app/api/` nhận request.
- `app/services/` xử lý logic.
- `app/repository/` làm việc với DB.
- `app/model/` là bảng dữ liệu.
- `app/schema/` là lớp kiểm tra dữ liệu.
- `app/core/` giữ cấu hình, auth, DI, DB.
- `tests/` kiểm tra toàn bộ chuỗi đó.

Đọc theo thứ tự này là dễ nhất: **main -> api -> service -> repository -> model -> db**.