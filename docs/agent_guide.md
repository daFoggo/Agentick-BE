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

---

## 4. Triết lý Thiết kế & Tối ưu hóa Agent (Theo chuẩn Anthropic: Building Effective Agents)

Hệ thống Agent trong **Agentick** được thiết kế, tối ưu hóa và vận hành dựa trên các nguyên tắc thực chiến tiên tiến nhất từ Anthropic nhằm đảm bảo tính tin cậy cao, hiệu năng vượt trội và tiết kiệm chi phí trong môi trường Production.

### 4.1. Giữ tính Đơn giản (Simplicity Over Heavy Frameworks)
* **Quy tắc Anthropic:** Tránh sử dụng các Agent Framework cồng kềnh (như LangChain, CrewAI) khi không cần thiết, vì chúng tạo ra các tầng trừu tượng che giấu Prompt thực tế và gây khó khăn khi debug.
* **Cách Agentick áp dụng:** 
  * Chúng ta tự xây dựng ReAct loop và kết nối trực tiếp OpenRouter qua thư viện `httpx` tại `CustomAgent`.
  * **Chương trình hóa điều kiện (Programmatic Gates):** Với tính năng **Agent Outreach**, thay vì bắt LLM tự suy luận xem có nên gửi email hay không (gây tốn token và không chính xác), chúng ta sử dụng code Python thuần trong `AgentOutreachService` để kiểm tra điều kiện (Task ở trạng thái todo/done, deadline xa hơn 3 ngày, đã gửi email trong 24h, hay thành viên hoạt động trong 2h gần nhất). LLM chỉ được gọi duy nhất ở bước cuối cùng khi thực sự cần trí tuệ nhân tạo để viết nội dung email cá nhân hóa.

### 4.2. Tối ưu hóa ACI (Agent-Computer Interface) & Thiết kế Chống lỗi (Poka-Yoke)
* **Quy tắc Anthropic:** Định nghĩa Tools (JSON Schema) cho LLM cần được đầu tư kỹ lưỡng giống như viết Docstring cho một lập trình viên Junior. Tối ưu hóa tham số để LLM không bao giờ truyền sai dữ liệu (Poka-yoke).
* **Cách Agentick áp dụng:**
  * Chúng ta rà soát và cấu trúc lại toàn bộ danh mục Tool trong [task_tools.py](file:///d:/Dev%20projects/Agentick-BE/app/tools/task_tools.py).
  * Khắc phục triệt để lỗi thiếu trường bắt buộc bằng cách đưa `start_date` và `due_date` trực tiếp vào schema của `create_task` với chỉ dẫn định dạng **ISO-8601** rõ ràng.
  * Chỉ định rõ ràng kiểu định dạng **UUID tuyệt đối** cho các trường khóa ngoại (`status_id`, `priority_id`, `type_id`, `project_id`) để tránh LLM tự suy đoán (hallucinate) hoặc truyền chuỗi ký tự tự do.
  * Tích hợp thêm trường `estimated_hours` trực tiếp vào Tool để AI chủ động ghi nhận thời gian ước lượng khi tạo Task, làm cơ sở dữ liệu ban đầu cho hệ thống dự báo rủi ro trễ hạn.

### 4.3. Đề cao tính Minh bạch (Prioritize Transparency)
* **Quy tắc Anthropic:** Giúp người dùng hiểu được các bước lập kế hoạch và suy nghĩ của Agent để xây dựng lòng tin lâu dài.
* **Cách Agentick áp dụng:**
  * Toàn bộ chuỗi suy nghĩ (Thought) và hành động gọi Tool đều được ghi lại tự động thông qua decorator `@track` của Opik và lưu trực tiếp trong cơ sở dữ liệu.
  * Các tín hiệu đánh giá rủi ro được lưu trữ chi tiết dưới dạng JSON trong trường `signals` của bảng `risk_snapshot` để hiển thị trực tiếp lên Frontend cho PM biết rõ *tại sao* Agent đánh giá Task này có rủi ro cao.

### 4.4. Mô hình Đánh giá - Tối ưu (Evaluator-Optimizer Workflow)
* **Quy tắc Anthropic:** Áp dụng mô hình một LLM sinh kết quả (Generator) và một LLM (hoặc dữ liệu phản hồi) kiểm tra tinh chỉnh (Evaluator) để nâng cao chất lượng đầu ra một cách vượt bậc.
* **Cách Agentick áp dụng:**
  * Trong lộ trình phân tích rủi ro trễ hạn nâng cao, Agentick sử dụng dữ liệu sai số thực tế giữa ước lượng ban đầu (`estimated_hours`) và thực tế thực thi (`actual_hours`) từ lịch sử hoạt động để làm Feedback Loop phản hồi cho Agent tinh chỉnh lại điểm số rủi ro (`risk_score`) trước khi đưa ra cảnh báo.

