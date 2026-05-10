import os

# Tự động nạp .env vào os.environ trước khi nạp opik
if os.path.exists(".env"):
    with open(".env", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

import httpx
from opik import track


def get_env_variable(var_name: str, default: str = None) -> str:
    # 1. Thử đọc từ biến môi trường hệ thống
    val = os.getenv(var_name)
    if val:
        return val

    # 2. Thử đọc trực tiếp từ file .env
    if os.path.exists(".env"):
        with open(".env", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{var_name}="):
                    # Bỏ phần định danh và dấu ngoặc kép nếu có
                    val = line.strip().split("=", 1)[1]
                    return val.strip('"').strip("'")
    return default


@track(entrypoint=True, project_name="Agentick")
def test_openrouter():

    api_key = get_env_variable("OPENROUTER_API_KEY")
    base_url = get_env_variable("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model_name = get_env_variable("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    if not api_key:
        print(
            "❌ LỖI: Không tìm thấy OPENROUTER_API_KEY trong môi trường hoặc file .env."
        )
        print("👉 Vui lòng thêm dòng sau vào file .env của bạn trước khi chạy:")
        print("   OPENROUTER_API_KEY=your_actual_key_here")
        return

    print("🔑 Đã tìm thấy API Key.")
    print(f"🤖 Model đang sử dụng: {model_name}")
    print(f"🌐 Base URL đang sử dụng: {base_url}")

    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://agentick.ai",
        "X-OpenRouter-Title": "Agentick Test",
    }
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": "Xin chào! Bạn là ai? Hãy trả lời ngắn gọn trong 1 câu.",
            }
        ],
    }

    print("⏳ Đang gửi request thử nghiệm tới OpenRouter...")
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=15.0)
        response.raise_for_status()
        res_json = response.json()
        reply = res_json["choices"][0]["message"]["content"]
        print("\n🎉 Kết quả kết nối OpenRouter thành công! 🎉")
        print(f"🤖 Phản hồi của AI: {reply}\n")
        return reply

    except Exception as e:
        print(f"\n❌ Lỗi khi gọi OpenRouter: {str(e)}")
        if "response" in locals() and response is not None:
            print(f"Trạng thái HTTP: {response.status_code}")
            print(f"Chi tiết: {response.text}")


if __name__ == "__main__":
    test_openrouter()
