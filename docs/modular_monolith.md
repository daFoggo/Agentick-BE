# Kiến trúc Triển khai: Modular Monolith trong Agentick-BE

Dự án **Agentick-BE** được thiết kế và vận hành theo mô hình **Modular Monolith** (Nguyên khối phân hệ). Đây là một chiến lược thiết kế kết hợp giữa sự đơn giản trong triển khai của kiến trúc Monolith (Nguyên khối) và tính tổ chức, độc lập cao của Microservices (Vi dịch vụ).

---

## 1. Modular Monolith là gì?

- **Monolith (Nguyên khối):** Toàn bộ ứng dụng được đóng gói và triển khai như một khối thống nhất duy nhất (một container, một process). Mọi thành phần đều chạy chung trên một process của hệ điều hành (trên Uvicorn/FastAPI).
- **Modular (Phân hệ/Mô-đun hóa):** Mã nguồn bên trong ứng dụng không bị viết dính liền (spaghetti code). Thay vào đó, nó được chia tách rạch ròi thành các module độc lập dựa theo Clean Architecture và Domain-Driven Design (VD: `task`, `project`, `user`, `team`). 

=> **Modular Monolith** có nghĩa là: Code được phân rã như Microservices, nhưng khi chạy thực tế lại gộp chung lại thành một ứng dụng duy nhất.

---

## 2. Dấu ấn Modular Monolith trong dự án Agentick

### 2.1. Đơn giản hóa việc Triển khai (Deployment)
Thay vì phải quản lý hàng chục CI/CD pipelines, cấu hình K8s phức tạp và service mesh như Microservices, Agentick-BE chỉ sử dụng một điểm vào duy nhất:
- **Entrypoint:** `app/main.py`.
- Toàn bộ backend được bọc gọn trong một Docker Image duy nhất.
- Triển khai nội bộ bằng một file `docker-compose.yml` duy nhất, khởi tạo đồng thời FastAPI (Backend), PostgreSQL (Database chính), và Qdrant (Vector Database).

### 2.2. Phân tách ranh giới mềm (Soft Boundaries)
Dù chạy chung một process, các Domain (Nghiệp vụ) không được phép "vượt rào" truy cập trực tiếp vào DB của nhau.
- Ví dụ: `TaskService` muốn lấy danh sách member của một dự án, nó **không** tự ý viết raw SQL truy vấn bảng `project_member`. Thay vào đó, `TaskService` phải gọi thông qua `ProjectMemberRepository` (hoặc `ProjectMemberService`) đã được tiêm vào (Dependency Inject) từ trước.
- **Lợi ích:** Các ranh giới (boundaries) được giữ gìn thông qua Interface/Service call. 

### 2.3. Chia sẻ tài nguyên dùng chung (Shared Resources)
Nhờ chạy trên một tiến trình duy nhất, các module có thể dễ dàng chia sẻ tài nguyên đắt đỏ (như Database Connection Pool) thông qua **Unit of Work**. Điều này đảm bảo tính ACID khi một giao dịch phải sửa dữ liệu ở cả 2 domain (VD: Tạo User mới và Tạo Team mặc định cùng một lúc). Khác với Microservices, khi đó ta sẽ phải đau đầu xử lý Distributed Transaction (Saga Pattern / 2PC).

---

## 3. Tại sao lại chọn Modular Monolith cho Agentick-BE?

Việc lựa chọn kiến trúc này thay vì Microservices mang lại những giá trị chiến lược:

1. **Hiệu suất (Performance):** Việc các module gọi nhau chỉ là các hàm gọi trong RAM (In-memory function calls), không có độ trễ mạng (Zero Network Latency), không tốn công chuyển đổi dữ liệu (Serialization/Deserialization) như REST API hay gRPC giữa các Microservices.
2. **Chi phí Vận hành (Ops/Infrastructure):** Tiết kiệm tối đa RAM và CPU. Không cần đội ngũ DevOps cồng kềnh để duy trì một cụm Kubernetes phức tạp.
3. **Dễ dàng gỡ lỗi (Debugging):** Quá trình debug (đặt breakpoint), tracing và đọc logs dễ dàng hơn rất nhiều vì luồng xử lý (stack trace) nằm gọn trong một service.
4. **Sẵn sàng tiến hóa (Evolutionary Architecture):** Trong tương lai, nếu một module (ví dụ: `LLM Agent` hoặc `Background Scheduler`) phình to hoặc cần scale độc lập, chúng ta hoàn toàn có thể "cắt" thư mục code đó ra thành một Microservice riêng biệt một cách rất dễ dàng vì ranh giới code (Clean Architecture) đã được thiết lập nghiêm ngặt từ ngày hôm nay.

---

## 4. Tóm lược

**Modular Monolith** tại Agentick-BE là sự cân bằng hoàn hảo. Nó mang lại **Tốc độ phát triển nhanh chóng** của Monolith ở giai đoạn hiện tại, đồng thời sở hữu **Thiết kế tinh gọn, sạch sẽ** sẵn sàng mở rộng (scale-out) thành Microservices khi sản phẩm đạt đến quy mô khổng lồ.
