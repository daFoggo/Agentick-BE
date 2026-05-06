# 🤖 Hướng dẫn cấu hình AI Agent & Opik Observability

Tài liệu này hướng dẫn chi tiết cách thiết lập, cấu hình và giám sát **AI Agent** trong dự án **Agentick Backend** sử dụng **OpenRouter** và **Opik Observability (Traces, Spans & Agent Playground)**.

---

## 1. Cấu hình AI Agent với OpenRouter

Dự án Agentick sử dụng **OpenRouter** để gọi động tới các mô hình ngôn ngữ lớn (LLM), ưu tiên mô hình mã nguồn mở miễn phí `openai/gpt-oss-120b:free`.

### Thiết lập biến môi trường `.env`
Thêm các biến môi trường sau vào cuối file `.env` của bạn:
```env
# --- CẤU HÌNH AI AGENT (OPENROUTER) ---
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-oss-120b:free
```

### Chạy thử nghiệm OpenRouter độc lập
Để kiểm tra kết nối tới OpenRouter đã hoạt động chính xác chưa, bạn chạy script thử nghiệm độc lập sau:
```bash
uv run scratch/test_openrouter.py
```
*Script sẽ tự động nạp `.env` và gọi thử nghiệm tới OpenRouter.*

---

## 2. Cấu hình Giám sát (LLM Observability) với Opik

**Opik** là nền tảng giám sát và tối ưu hóa hiệu suất LLM hàng đầu thế giới của Comet, giúp theo dõi chi tiết toàn bộ chu trình cuộc gọi (Trace) và hành động gọi tool (Spans) của Agent.

### Các biến môi trường của Opik
Cấu hình các dòng sau vào file `.env`:
```env
# --- CẤU HÌNH OPIK LLM OBSERVABILITY ---
OPIK_API_KEY=your_opik_api_key_here
OPIK_PROJECT_NAME=Agentick
```

### Bước 1: Đăng nhập và cấu hình Opik
Chạy lệnh sau tại thư mục dự án và làm theo hướng dẫn trên terminal để liên kết tài khoản Opik của bạn:
```bash
uv run opik configure
```
*Nhập khóa API Key từ tài khoản Opik của bạn (mục Settings của Opik).*

### Bước 2: Kích hoạt Agent Playground (Kết nối Tunnel)
Để sử dụng **Agent Playground** trực quan trên giao diện Web của Opik (cho phép chat thử nghiệm, tinh chỉnh prompt và thay đổi model trực tuyến), bạn cần mở một đường dẫn an toàn (tunnel) kết nối ngược từ Opik Cloud xuống server local của bạn.

Chạy lệnh sau trong PowerShell hoặc Terminal mới để khởi chạy server kèm tunnel:
```bash
uv run opik endpoint --project "Agentick" -- uv run uvicorn app.main:app --port 8000 --reload
```
**Kết quả:** Giao diện Opik Web sẽ hiển thị trạng thái **Status: Paired ✔ (Connected)**. Bạn có thể bấm chat và thử nghiệm prompt trực tiếp trên trình duyệt!

---

## 3. Cách thức hoạt động trong Code

### Đăng ký Decorator `@track`
Trong tệp [agent_service.py](file:///d:/Dev%20projects/Agentick-BE/app/services/agent_service.py), các decorator `@track` của Opik đã được tích hợp sẵn:

* **Trace cha (Điểm bắt đầu)**: Hàm `run_agent()` được bọc bằng `@track(entrypoint=True, name="run_agent_loop", project_name="Agentick")`.
* **Span con (Thực thi Tool)**: Hàm `execute_tool()` được bọc bằng `@track(name="execute_tool")` để ghi lại lịch sử gọi hàm tạo/sửa đổi Task trong cơ sở dữ liệu.

Khi gọi API `/api/v1/agent/chat` hoặc chạy thử nghiệm, Opik sẽ vẽ lại **sơ đồ cây (Span Tree)** tuyệt đẹp giúp bạn biết chính xác thời gian xử lý, chi phí token và kết quả gọi Tool.
