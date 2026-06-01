# MurmurAI

A Windows voice-to-text dictation app that transcribes speech locally using OpenAI's Whisper model and pastes the result into whatever window you are typing in — no internet or API key required.

---

## Features

- **Global hotkey** — press `Ctrl+Shift+Space` from anywhere to start/stop recording (fully customizable)
- **Local transcription** — Whisper small model runs entirely on your machine; nothing leaves your device
- **Works everywhere** — pastes into any app: browsers, editors, VS Code (editor and terminal), Notepad, Office, terminals
- **Language support** — auto-detect or pin to any of 60+ languages
- **System tray** — lives quietly in the tray; hotkey works even when the window is hidden
- **Dark UI** — small card window with recording state indicator

---

## Requirements

- Windows 10 / 11
- Python 3.11+
- ~500 MB disk space (Whisper small model, downloaded on first run)
- A microphone

---

## Installation

```bash
git clone https://github.com/tanyatripathi1198/MurmurAI
cd MurmurAI
pip install -r requirements.txt
```

First run downloads the Whisper model (~500 MB) automatically.

---

## Running

```bash
python src/main.py
```

The app appears as a small card window and a tray icon (bottom-right taskbar).

---

## Usage

| Action | How |
|---|---|
| Start recording | Press `Ctrl+Shift+Space` (or click the mic button) |
| Stop recording | Press `Ctrl+Shift+Space` again |
| Change hotkey | Click ⚙ → Hotkey field → press your combo → Save |
| Change language | Click ⚙ → Language dropdown → Save |
| Hide to tray | Close the window |
| Restore | Click the tray icon |
| Quit | Right-click tray icon → Quit |

After stopping, text is pasted into whatever window has focus with a leading space to separate it from existing text.

---

## How it works

```
Microphone (native device rate)
  → sounddevice (energy-based VAD)
  → scipy polyphase resample to 16kHz
  → faster-whisper (Whisper small, int8, CPU)
  → pyperclip + Shift+Insert paste
  → Active window
```

VAD fires after ~1 second of silence, sending the phrase to Whisper. Transcription takes ~70ms on a modern CPU. Total end-to-end latency is roughly 1–1.5 seconds after you finish speaking.

---

## Building a standalone `.exe`

```bash
pip install pyinstaller
pyinstaller murmurai.spec
# Output: dist/MurmurAI.exe
```

---

## Tech stack

| Package | Purpose |
|---|---|
| `faster-whisper` | Local speech-to-text (CTranslate2 backend) |
| `sounddevice` | Microphone capture at native device rate |
| `scipy` | Polyphase audio resampling (44.1/48kHz → 16kHz) |
| `numpy` | Audio buffer math |
| `customtkinter` | Dark-theme UI |
| `pynput` | Global hotkey listener |
| `pystray` | System tray icon |
| `Pillow` | Tray icon rendering |
| `pyperclip` | Clipboard write |
| `pyautogui` | Shift+Insert paste simulation |

---

## Running tests

```bash
python -m pytest tests/ -v
```

36 unit tests covering settings, audio VAD, transcription, text injection, hotkey, and the controller state machine.

---

## Settings file

Stored at `%APPDATA%\MurmurAI\settings.json`:

```json
{
  "hotkey": "ctrl+shift+space",
  "language": "auto",
  "start_on_login": false
}
```

---

## Limitations

- Windows only
- CPU transcription: ~1–1.5s latency per phrase (GPU would be near-instant)
- Whisper small model: good accuracy for clear speech; struggles with heavy accents or very fast speech
- VS Code terminal: uses `Shift+Insert` paste (standard), which works in most terminal emulators
