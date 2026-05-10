# 1. Tổng quan Dự án (Project Overview)

## 1.1. Tên dự án & Mục tiêu
- **Tên dự án**: Agentick
- **Định nghĩa**: Agentick là một nền tảng quản lý công việc thông minh được hỗ trợ bởi AI Agent. Khác với những công cụ truyền thống chỉ ghi chép thông tin, Agentick có tính "chủ động" cao. Hệ thống liên tục theo dõi tiến độ, xem xét lịch làm việc thực tế của từng người và đưa ra dự báo sớm nếu có nguy cơ trễ hạn.
- **Mục tiêu chính**:
  - **Không chỉ dừng lại ở dữ liệu tĩnh**: Kết hợp giữa việc tính toán số liệu (giờ làm, tiến độ) và trí tuệ nhân tạo (AI) để đưa ra đánh giá sát thực tế nhất.
  - **Dự báo thông minh hơn theo thời gian**: Hệ thống biết tự nhìn lại xem trong quá khứ nhân sự hay ước lượng sai bao nhiêu giờ, từ đó tự động cộng trừ sai số để dự đoán lần sau chính xác hơn.
  - **Hỗ trợ hành động trực tiếp**: Trợ lý AI phân tích tự động soạn thảo email nhắc nhở gửi cảnh báo tức thời cho các thành viên liên quan khi phát hiện nguy cấp.

## 1.2. Phạm vi chi tiết (Detailed Scope)

### Quản lý thời gian và Lịch trình
- Cho phép mỗi người dùng tự cài đặt giờ làm việc cụ thể mỗi ngày trong tuần.
- Tổng hợp toàn bộ sự kiện và lịch họp để AI biết chính xác một người còn trống bao nhiêu tiếng để làm việc.

### Vận hành Dự án đa dạng góc nhìn
- Cung cấp cách xem công việc linh hoạt phù hợp nhu cầu: **Bảng Kanban** (kéo thả trạng thái trực quan) và **Dạng danh sách** (dễ dàng lọc và tìm kiếm dữ liệu).
- Cho phép tùy chỉnh sâu cấu trúc của dự án: Tự tạo bộ Trạng thái (Status) riêng biệt, phân loại công việc (Task Type) kèm icon đại diện, gắn nhãn (Tags) và cài đặt mức độ ưu tiên theo màu sắc riêng.

### Bộ não AI phân tích rủi ro (Lõi thông minh)
- **Báo cáo trực quan (Risk Dashboard)**: Hiển thị trực quan mức độ nguy hiểm toàn dự án thông qua Biểu đồ phân bổ ma trận và Đồng hồ đo điểm rủi ro.
- **Tự động quét các dấu hiệu rủi ro**: Hệ thống tự động thu thập và đánh giá các tín hiệu quan trọng:
  1. **Độ chênh lệch thời gian**: So sánh giờ làm thực tế và giờ ước lượng.
  2. **Kiểm tra quỹ thời gian**: Tự đếm xem từ nay đến hạn chót nhân sự còn bao nhiêu giờ trống dựa trên lịch cá nhân.
  3. **Mật độ công việc (Congestion)**: Đếm số lượng task đang chạy song song cùng lúc của một nhân sự.
  4. **Tự động bù trừ sai số**: Dựa vào tỷ lệ thường xuyên ước lượng sai trong quá khứ của nhân sự để hiệu chuẩn lại kết quả hiện tại.
- **Gửi cảnh báo tự động**: AI tổng hợp số liệu thành khuyến nghị văn bản và tự kích hoạt gửi Email thông báo khẩn cấp khi rủi ro vượt ngưỡng an toàn.

## 1.3. Chi tiết Tech Stack kỹ thuật

### Backend Architecture (Phía Máy chủ)
- **Ngôn ngữ & Core**: Python 3.12+, sử dụng framework **FastAPI** (bất đồng bộ Async) giúp xử lý tác vụ cực nhanh. Quản lý package tốc độ cao qua công cụ **UV**.
- **Cơ sở dữ liệu**: **PostgreSQL 16** đảm bảo dữ liệu an toàn, sử dụng **SQLAlchemy 2.0** (ORM) thế hệ mới nhất cho khả năng bắt lỗi kiểu dữ liệu chặt chẽ, kết hợp với **Alembic** để quản lý lịch sử cập nhật cấu trúc DB.
- **Tầng xử lý AI**: 
  - **OpenRouter API**: Cổng kết nối thông minh giúp dễ dàng hoán đổi qua lại các dòng AI lớn nhất thế giới hiện nay.
  - **Opik Observability**: Hệ thống ghi vết hoạt động của AI, đếm lượng Token tiêu hao và debug lỗi kịp thời.
- **Bảo mật**: Chứng thực qua **JWT Bearer Token** (bao gồm cơ chế làm mới Access/Refresh token) kết hợp băm mật khẩu chuyên dụng `pwdlib`.
- **Vận hành**: Chạy trên nền tảng container hóa của **Docker** và **Docker Compose**.
- **Chất lượng code**: Sử dụng bộ công cụ **Ruff** để định dạng code và phát hiện lỗi nhanh và chính xác.

### Frontend Engineering (Phía Giao diện)
- **Nền tảng cốt lõi**: **TanStack Start** (Full-stack framework xây dựng trên nền React & Vite), sử dụng hoàn toàn **TypeScript** để đảm bảo mã nguồn an toàn, ít lỗi runtime.
- **Quản trị Giao diện**: 
  - Cấu hình Layout qua **TanStack Router** theo chuẩn File-based.
  - Xử lý Form dữ liệu thông qua **TanStack Form** kết hợp thư viện kiểm duyệt **Zod**.
- **Quản lý dữ liệu & Giao diện**: 
  - Lưu nhớ tạm thời dữ liệu (Server caching) qua **TanStack Query** giúp tăng tốc tải trang tức thì.
  - Thiết kế UI theo phong cách hiện đại của **Tailwind CSS** và thư viện thành phần **Shadcn UI**.
  - Quản lý trạng thái toàn cục bằng **Zustand**.
- **Chất lượng code**: Sử dụng bộ công cụ **Biome** (thay thế cho ESLint/Prettier) mang lại tốc độ định dạng code và phát hiện lỗi nhanh gấp hàng chục lần.
