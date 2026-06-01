# Novaa AI

A Windows voice-to-text dictation app that transcribes speech locally using OpenAI's Whisper model and pastes the result into whatever window you are typing in — no internet or API key required.

---

## Features

- **Global hotkey** — press `Ctrl+Shift+Space` from anywhere to start/stop recording (fully customizable)
- **Wake word** — say "Hey Nova" to start recording hands-free (requires OpenWakeWord model file)
- **Local transcription** — Whisper small model runs entirely on your machine; nothing leaves your device
- **Works everywhere** — pastes into any app: browsers, editors, VS Code (editor and terminal), Notepad, Office, terminals
- **Language support** — auto-detect or pin to any of 60+ languages
- **System tray** — lives quietly in the tray; hotkey works even when the window is hidden
- **Elegant UI** — minimal dark card with N logo, state-aware mic button, sound feedback
- **Sound effects** — ascending beep on recording start, low beep on stop

---

## Requirements

- Windows 10 / 11
- Python 3.11+
- ~500 MB disk space (Whisper small model, downloaded on first run)
- A microphone

---

## Installation

```bash
git clone https://github.com/tanyatripathi1198/NovaaAI
cd NovaaAI
pip install -r requirements.txt
```

First run downloads the Whisper model (~500 MB) automatically.

---

## Running

```bash
python src/main.py
```

The app appears as a small card window and an N-logo tray icon (bottom-right taskbar).

---

## Usage

| Action | How |
|---|---|
| Start recording | Press `Ctrl+Shift+Space` (or click the mic button) |
| Stop recording | Press `Ctrl+Shift+Space` again |
| Wake word | Say "Hey Nova" — recording starts automatically |
| Change hotkey | Click ⚙ → Hotkey field → press your combo → Save |
| Change language | Click ⚙ → Language dropdown → Save |
| Enable wake word | Click ⚙ → toggle "Wake word (Hey Nova)" → Save |
| Hide to tray | Close the window |
| Restore | Click the tray icon |
| Quit | Right-click tray icon → Quit |

After stopping, text is pasted into whatever window has focus with a leading space to separate it from existing text.

---

## How it works

```
Microphone (native device rate, e.g. 44.1kHz)
  → sounddevice (energy-based VAD, fires after 500ms silence)
  → scipy polyphase resample to 16kHz
  → faster-whisper (Whisper small, int8, CPU)
  → pyperclip + Shift+Insert paste
  → Active window
```

VAD fires 500ms after speech ends, triggering transcription (~2.5s on CPU). Total end-to-end latency is roughly 3–4 seconds after you finish speaking on CPU hardware.

**Wake word mode:** OpenWakeWord runs a separate background audio stream, detects "Hey Nova", and starts recording with a 1.5s silence window (auto-stops after phrase).

---

## Wake word setup

1. Place your `.tflite` model file at `%APPDATA%\NovaaAI\` (e.g. `Hey_Nova_20260328_194345.tflite`)
2. Open Novaa AI settings → toggle **"Wake word (Hey Nova)"** → Save
3. Say **"Hey Nova"** — recording starts, text appears after a 1.5s pause

The app uses [OpenWakeWord](https://github.com/dscripka/openWakeWord) with TFLite inference. Requires `ai-edge-litert` (installed via requirements.txt).

---

## Building a standalone `.exe`

```bash
pip install pyinstaller
pyinstaller novaaai.spec
# Output: dist/NovaaAI.exe
```

---

## Tech stack

| Package | Purpose |
|---|---|
| `faster-whisper` | Local speech-to-text (CTranslate2 backend) |
| `sounddevice` | Microphone capture at native device rate |
| `scipy` | Polyphase audio resampling (44.1/48kHz → 16kHz) |
| `numpy` | Audio buffer math |
| `customtkinter` | Elegant dark UI |
| `pynput` | Global hotkey listener |
| `pystray` | System tray icon |
| `Pillow` | N-logo icon rendering |
| `pyperclip` | Clipboard write |
| `pyautogui` | Shift+Insert paste simulation |
| `openwakeword` | Wake word detection engine |
| `ai-edge-litert` | TFLite runtime for wake word models |

---

## Running tests

```bash
python -m pytest tests/ -v
```

48 unit tests covering settings, audio VAD, transcription, text injection, hotkey, controller state machine, and wake word listener.

---

## Settings file

Stored at `%APPDATA%\NovaaAI\settings.json`:

```json
{
  "hotkey": "ctrl+shift+space",
  "language": "auto",
  "start_on_login": false,
  "wake_word_enabled": false
}
```

---

## Limitations

- Windows only
- CPU transcription: ~2.5s fixed overhead per phrase (Whisper always processes a 30s internal window); GPU would be near-instant
- Whisper small model: good accuracy for clear speech; may struggle with heavy accents or very fast speech
- Wake word model quality depends on training data; test with `python test_wakeword.py` if detection is poor
