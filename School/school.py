"""SCHOOL — trợ lý ảo điều khiển Mac và internet bằng giọng nói hoặc gõ phím.

Chạy:  ./run.sh            (nói chuyện bằng giọng)
       ./run.sh --text     (chỉ gõ phím)
"""
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

import anthropic  # noqa: E402

import tools  # noqa: E402

MODEL = os.getenv("SCHOOL_MODEL", "claude-sonnet-5-5")
MAX_HISTORY = 40

PERSONA = """Bạn là SCHOOL, trợ lý ảo trung thành và thông minh, phong cách như SCHOOL của Tony Stark.
Gọi người dùng là "Sếp". Trả lời bằng tiếng Việt, ngắn gọn, đi thẳng vào trọng tâm, có chút dí dỏm nhẹ.
Câu trả lời sẽ được đọc thành tiếng: KHÔNG dùng markdown, bảng, emoji, danh sách dài.
Khi Sếp yêu cầu hành động (mở app, tìm thông tin, chạy lệnh, gọi điện...), hãy dùng công cụ để làm ngay.
Với việc có rủi ro, hệ thống sẽ hỏi xác nhận; nếu bị từ chối thì tôn trọng và đề xuất cách khác.
Khi Sếp nói điều quan trọng về bản thân, dự án, sở thích, hãy dùng công cụ remember để ghi nhớ."""


def build_system() -> str:
    parts = [PERSONA, f"Bây giờ là {datetime.now():%A %d/%m/%Y %H:%M}."]
    memory = tools.load_memory()
    if memory:
        parts.append("Những điều đã ghi nhớ về Sếp:\n" + memory)
    return "\n\n".join(parts)


def trim_history(history: list) -> None:
    """Giữ lịch sử gần nhất, cắt tại một tin nhắn người dùng dạng chữ để không làm hỏng cặp tool_use/tool_result."""
    if len(history) <= MAX_HISTORY:
        return
    start = len(history) - MAX_HISTORY
    while start < len(history) and not (
        history[start]["role"] == "user" and isinstance(history[start]["content"], str)
    ):
        start += 1
    del history[:start]


def ask_claude(client: anthropic.Anthropic, history: list, user_text: str) -> str:
    history.append({"role": "user", "content": user_text})
    while True:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=build_system(),
            tools=tools.TOOL_SCHEMAS,
            messages=history,
        )
        history.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "pause_turn":  # server web_search chạy lâu, tiếp tục
            continue
        if resp.stop_reason != "tool_use":
            trim_history(history)
            return "".join(b.text for b in resp.content if b.type == "text").strip()

        results = []
        for block in resp.content:
            if block.type == "tool_use":
                print(f"  ⚙️  {block.name}({block.input})")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": tools.dispatch(block.name, block.input),
                })
        history.append({"role": "user", "content": results})


def main() -> None:
    from voice import speak

    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Thiếu ANTHROPIC_API_KEY trong School/.env")

    text_mode = "--text" in sys.argv
    client = anthropic.Anthropic()
    history: list = []

    if not text_mode:
        import voice  # noqa: F401  (kiểm tra sớm thư viện âm thanh)
        if not os.getenv("OPENAI_API_KEY"):
            sys.exit("Thiếu OPENAI_API_KEY (dùng cho nhận dạng giọng nói) trong School/.env. Hoặc chạy với --text.")

    speak("SCHOOL trực tuyến. Sẵn sàng phục vụ Sếp.")
    print("Enter: nói chuyện  |  Gõ chữ rồi Enter: nhập bằng bàn phím  |  q: thoát")

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if line.lower() in ("q", "quit", "exit", "thoát"):
            speak("Tạm biệt Sếp.")
            break

        if line:
            user_text = line
        elif text_mode:
            continue
        else:
            from voice import record, transcribe

            wav = record()
            if wav is None:
                print("(Không nghe thấy gì)")
                continue
            user_text = transcribe(wav)
            print(f"🗣  Sếp: {user_text}")
            if not user_text:
                continue

        try:
            reply = ask_claude(client, history, user_text)
        except anthropic.APIError as e:
            reply = f"Xin lỗi Sếp, tôi gặp lỗi kết nối tới bộ não: {e}"
        speak(reply or "Tôi chưa có gì để nói, Sếp.")


if __name__ == "__main__":
    main()
