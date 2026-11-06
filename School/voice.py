"""Giọng nói: thu âm từ micro, chuyển thành chữ (Whisper), đọc to (macOS `say`)."""
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np

SAMPLE_RATE = 16000
BLOCK_SECS = 0.1
SILENCE_THRESHOLD = float(os.getenv("JARVIS_SILENCE", "500"))  # tăng nếu phòng ồn
END_SILENCE_SECS = 1.2   # im lặng bao lâu thì coi như đã nói xong
WAIT_FOR_SPEECH_SECS = 8  # chờ người nói tối đa bao lâu
MAX_SPEECH_SECS = 30


def record() -> str | None:
    """Thu âm đến khi người dùng im lặng. Trả về đường dẫn file wav, hoặc None nếu không nói gì."""
    import sounddevice as sd

    block = int(SAMPLE_RATE * BLOCK_SECS)
    frames, started, silent_for, elapsed = [], False, 0.0, 0.0
    print("🎙  Đang nghe... (Sếp cứ nói, im lặng là JARVIS xử lý)")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        while elapsed < MAX_SPEECH_SECS:
            data, _ = stream.read(block)
            frames.append(data.copy())
            elapsed += BLOCK_SECS
            rms = float(np.sqrt(np.mean(data.astype(np.float32) ** 2)))
            if rms > SILENCE_THRESHOLD:
                started, silent_for = True, 0.0
            elif started:
                silent_for += BLOCK_SECS
                if silent_for >= END_SILENCE_SECS:
                    break
            elif elapsed >= WAIT_FOR_SPEECH_SECS:
                return None
    audio = np.concatenate(frames)
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(audio.tobytes())
    return path


def transcribe(path: str) -> str:
    from openai import OpenAI

    with open(path, "rb") as f:
        result = OpenAI().audio.transcriptions.create(model="whisper-1", file=f, language="vi")
    os.remove(path)
    return result.text.strip()


def speak(text: str) -> None:
    print(f"\n🤖 JARVIS: {text}\n")
    if sys.platform == "darwin":
        voice = os.getenv("JARVIS_VOICE", "Linh")
        rate = os.getenv("JARVIS_RATE", "190")
        subprocess.run(["say", "-v", voice, "-r", rate, text])
