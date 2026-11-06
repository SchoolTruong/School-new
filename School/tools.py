"""Công cụ của JARVIS: điều khiển Mac, đọc web, gọi điện, ghi nhớ.

Hành động có rủi ro (chạy lệnh, ghi file, AppleScript, gọi điện) luôn hỏi xác nhận
trước khi làm. Đặt JARVIS_AUTO_APPROVE=1 để bỏ qua xác nhận (không khuyến nghị).
"""
import base64
import html
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent
MEMORY_FILE = BASE_DIR / "memory.md"
MAX_OUT = 6000


def _confirm(action: str) -> bool:
    if os.getenv("JARVIS_AUTO_APPROVE") == "1":
        return True
    ans = input(f"\n⚠️  JARVIS muốn: {action}\n   Cho phép? [y/N] ").strip().lower()
    return ans in ("y", "yes", "c", "có", "co")


def _trim(text: str) -> str:
    return text if len(text) <= MAX_OUT else text[:MAX_OUT] + "\n...[đã cắt bớt]"


def _applescript_str(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


# ---------- Hệ thống Mac ----------

def run_shell(command: str) -> str:
    if not _confirm(f"chạy lệnh shell: {command}"):
        return "Sếp đã từ chối lệnh này."
    p = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    out = (p.stdout + ("\n[stderr]\n" + p.stderr if p.stderr else "")).strip()
    return _trim(f"exit={p.returncode}\n{out}")


def run_applescript(script: str) -> str:
    if not _confirm("chạy AppleScript:\n" + script):
        return "Sếp đã từ chối."
    p = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=60)
    return _trim((p.stdout or p.stderr).strip() or "OK")


def open_app(app_name: str) -> str:
    p = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
    return "Đã mở " + app_name if p.returncode == 0 else f"Không mở được {app_name}: {p.stderr.strip()}"


def set_volume(level: int) -> str:
    level = max(0, min(100, int(level)))
    return run_applescript(f"set volume output volume {level}")


def notify(title: str, message: str) -> str:
    script = f"display notification {_applescript_str(message)} with title {_applescript_str(title)}"
    subprocess.run(["osascript", "-e", script], capture_output=True)
    return "Đã hiện thông báo."


def read_file(path: str) -> str:
    p = Path(path).expanduser()
    return _trim(p.read_text(encoding="utf-8", errors="replace"))


def write_file(path: str, content: str) -> str:
    p = Path(path).expanduser()
    if not _confirm(f"ghi file {p} ({len(content)} ký tự)"):
        return "Sếp đã từ chối ghi file."
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"Đã ghi {p}"


# ---------- Internet ----------

def fetch_url(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        raw = r.read().decode("utf-8", errors="replace")
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return _trim(text)


def make_phone_call(to: str, message: str) -> str:
    """Gọi điện qua Twilio và đọc một đoạn thông điệp (một chiều)."""
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    sender = os.getenv("TWILIO_FROM_NUMBER")
    if not all([sid, token, sender]):
        return "Chưa cấu hình Twilio (TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN / TWILIO_FROM_NUMBER)."
    if not _confirm(f"gọi điện tới {to} và đọc: “{message}”"):
        return "Sếp đã từ chối cuộc gọi."
    twiml = f"<Response><Say>{html.escape(message)}</Say></Response>"
    data = urllib.parse.urlencode({"To": to, "From": sender, "Twiml": twiml}).encode()
    req = urllib.request.Request(
        f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Calls.json", data=data
    )
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    return f"Đã gọi {to}, trạng thái: {body.get('status')}"


# ---------- Ghi nhớ ----------

def remember(note: str) -> str:
    with MEMORY_FILE.open("a", encoding="utf-8") as f:
        f.write(f"- {note}\n")
    return "Đã ghi nhớ."


def load_memory() -> str:
    return MEMORY_FILE.read_text(encoding="utf-8") if MEMORY_FILE.exists() else ""


# ---------- Đăng ký công cụ ----------

REGISTRY = {
    "run_shell": run_shell,
    "run_applescript": run_applescript,
    "open_app": open_app,
    "set_volume": set_volume,
    "notify": notify,
    "read_file": read_file,
    "write_file": write_file,
    "fetch_url": fetch_url,
    "make_phone_call": make_phone_call,
    "remember": remember,
}

TOOL_SCHEMAS = [
    # Tìm kiếm web do Anthropic thực thi phía server
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 5},
    {
        "name": "run_shell",
        "description": "Chạy lệnh shell trên Mac (cần Sếp xác nhận).",
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
    },
    {
        "name": "run_applescript",
        "description": "Chạy AppleScript để điều khiển ứng dụng macOS (cần xác nhận).",
        "input_schema": {"type": "object", "properties": {"script": {"type": "string"}}, "required": ["script"]},
    },
    {
        "name": "open_app",
        "description": "Mở một ứng dụng trên Mac theo tên, ví dụ 'Safari', 'Visual Studio Code'.",
        "input_schema": {"type": "object", "properties": {"app_name": {"type": "string"}}, "required": ["app_name"]},
    },
    {
        "name": "set_volume",
        "description": "Đặt âm lượng Mac từ 0 đến 100.",
        "input_schema": {"type": "object", "properties": {"level": {"type": "integer"}}, "required": ["level"]},
    },
    {
        "name": "notify",
        "description": "Hiện thông báo trên màn hình Mac.",
        "input_schema": {
            "type": "object",
            "properties": {"title": {"type": "string"}, "message": {"type": "string"}},
            "required": ["title", "message"],
        },
    },
    {
        "name": "read_file",
        "description": "Đọc nội dung một file văn bản trên Mac.",
        "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    },
    {
        "name": "write_file",
        "description": "Ghi nội dung vào file trên Mac (cần xác nhận).",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Tải và đọc nội dung chữ của một trang web.",
        "input_schema": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]},
    },
    {
        "name": "make_phone_call",
        "description": "Gọi điện tới số điện thoại (E.164, ví dụ +84901234567) và đọc một thông điệp. Cần xác nhận.",
        "input_schema": {
            "type": "object",
            "properties": {"to": {"type": "string"}, "message": {"type": "string"}},
            "required": ["to", "message"],
        },
    },
    {
        "name": "remember",
        "description": "Ghi nhớ một thông tin lâu dài về Sếp (sở thích, dự án, lịch...).",
        "input_schema": {"type": "object", "properties": {"note": {"type": "string"}}, "required": ["note"]},
    },
]


def dispatch(name: str, args: dict) -> str:
    fn = REGISTRY.get(name)
    if fn is None:
        return f"Không có công cụ '{name}'."
    try:
        return str(fn(**args))
    except Exception as e:  # trả lỗi về cho Claude để tự xử lý
        return f"Lỗi khi chạy {name}: {e}"
