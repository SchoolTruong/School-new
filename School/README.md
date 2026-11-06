# JARVIS — trợ lý ảo cho Mac

Nói chuyện bằng giọng hoặc gõ phím. JARVIS có thể:

- Tìm thông tin trên internet, đọc nội dung trang web
- Mở ứng dụng, chỉnh âm lượng, hiện thông báo, điều khiển app bằng AppleScript
- Chạy lệnh shell và đọc/ghi file trên Mac
- Gọi điện thoại và đọc một thông điệp (qua Twilio)
- Ghi nhớ thông tin về bạn giữa các lần chạy

Mọi hành động có rủi ro (chạy lệnh, ghi file, AppleScript, gọi điện) đều **hỏi xác nhận `y/N` trước khi làm**.

## Cài đặt (một lần)

1. Cần Mac có Python 3.10+ (`python3 --version`).
2. Lấy API key:
   - **Anthropic** (bắt buộc): https://console.anthropic.com
   - **OpenAI** (bắt buộc nếu nói bằng giọng, dùng Whisper để nhận dạng tiếng Việt): https://platform.openai.com
3. Trong thư mục `School/`, chạy:
   ```bash
   ./run.sh
   ```
   Lần đầu sẽ tạo `.env` và mở file. Điền `ANTHROPIC_API_KEY` và `OPENAI_API_KEY`, lưu, rồi chạy lại `./run.sh`.
4. Cấp quyền khi macOS hỏi: **Microphone** cho Terminal (System Settings → Privacy & Security → Microphone).

## Cách dùng

```bash
./run.sh            # chế độ giọng nói
./run.sh --text     # chế độ gõ phím
```

- Nhấn **Enter** rồi nói. Im lặng khoảng 1 giây là JARVIS xử lý.
- Hoặc gõ thẳng câu lệnh rồi Enter.
- Gõ `q` để thoát.

Ví dụ: "Mở Safari", "Tìm giá vàng hôm nay", "Đặt âm lượng 30", "Nhắc tôi tối nay gọi cho mẹ", "Gọi +84901234567 nhắn là tôi đang trên đường".

## Gọi điện (tuỳ chọn)

Cần tài khoản Twilio, có số điện thoại và điền 3 biến `TWILIO_*` trong `.env`.
- Tài khoản dùng thử chỉ gọi được tới số đã xác minh trong Twilio Console.
- Hiện tại JARVIS **đọc một thông điệp một chiều**. Đàm thoại hai chiều qua điện thoại cần thêm webhook server và giọng nói thời gian thực. Đây là bước nâng cấp tiếp theo nếu bạn muốn.

## Tuỳ chỉnh

Các biến trong `.env`: giọng đọc (`JARVIS_VOICE`, xem `say -v '?'`), tốc độ (`JARVIS_RATE`), ngưỡng im lặng (`JARVIS_SILENCE`, tăng nếu phòng ồn), model (`JARVIS_MODEL`).

Thêm công cụ mới: viết hàm trong `tools.py`, thêm vào `REGISTRY` và `TOOL_SCHEMAS`.

## Lưu ý an toàn

- `JARVIS_AUTO_APPROVE=1` bỏ qua xác nhận. Không nên bật.
- `memory.md` và `.env` là dữ liệu riêng tư, đã được đưa vào `.gitignore`.
