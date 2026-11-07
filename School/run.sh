#!/usr/bin/env bash
# Cài đặt lần đầu và khởi chạy SCHOOL. Dùng: ./run.sh  hoặc  ./run.sh --text
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Đã tạo School/.env. Hãy mở file này, điền API key rồi chạy lại."
  open -e .env 2>/dev/null || true
  exit 0
fi

if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi

if [ "$(uname)" = "Darwin" ]; then
  # sounddevice cần PortAudio; cài một lần qua Homebrew nếu có
  if ! brew list portaudio >/dev/null 2>&1 && command -v brew >/dev/null; then
    brew install portaudio >/dev/null
    .venv/bin/pip install -q --force-reinstall sounddevice
  fi
fi

exec .venv/bin/python school.py "$@"
