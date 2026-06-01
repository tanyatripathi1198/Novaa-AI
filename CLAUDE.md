# MurmurAI — Claude Code Guide

## Project overview

Windows voice-to-text dictation app. Press a hotkey → speak → text is pasted wherever the cursor is. All transcription runs locally via Whisper (faster-whisper). No cloud, no API key.

## Running the app

```bash
python src/main.py
```

First launch: downloads Whisper small model (~500MB) to `%APPDATA%\MurmurAI\models\`. Subsequent launches skip the download.

## Running tests

```bash
python -m pytest tests/ -v        # all 36 tests
python -m pytest tests/test_X.py  # single module
```

All tests run without a microphone, GPU, or real audio — hardware is mocked.

## Project structure

```
src/
  main.py          — entry point, wires all components together
  controller.py    — state machine: IDLE → RECORDING → TYPING → IDLE
  audio.py         — microphone capture + energy VAD + polyphase resample
  transcriber.py   — faster-whisper wrapper
  injector.py      — clipboard paste via Shift+Insert
  hotkey.py        — pynput GlobalHotKeys for system-wide hotkey
  tray.py          — pystray system tray icon
  ui.py            — CustomTkinter card window + settings panel
  settings.py      — JSON settings load/save (%APPDATA%\MurmurAI\settings.json)
  model_manager.py — model download guard (marker file + .bin check)
tests/
  test_*.py        — unit tests per module, all hardware mocked
```

## Architecture

Single Python process. Four layers:

1. **UI** (main thread) — CustomTkinter window + pystray tray
2. **Controller** (main thread) — state machine, RLock for thread safety
3. **Audio + Transcription** (background thread) — sounddevice → VAD → faster-whisper
4. **Text injection** (background thread) — pyperclip + Shift+Insert

UI updates always go through `window.after(0, ...)` to stay on the main thread.

## Key tuning constants

`src/audio.py`:
- `_SILENCE_THRESHOLD = 0.008` — mic noise floor on this machine peaks at 0.0055 RMS; threshold is safely above that
- `_SILENCE_BLOCKS_TO_END = 10` — 1 second of silence ends a phrase; reducing this causes mid-sentence splits
- `_MIN_SPEECH_BLOCKS = 5` — 500ms minimum actual speech; prevents noise bursts from triggering transcription

`src/transcriber.py`:
- `beam_size=5` — best accuracy for clear speech on CPU; reducing improves speed but hurts accuracy
- `vad_filter=True, min_silence_duration_ms=500` — strips trailing silence from phrases, prevents Whisper hallucinations
- `condition_on_previous_text=False` — each phrase is independent, prevents repetition artifacts
- Confidence filter: `no_speech_prob < 0.6` — Whisper's own signal; filters hallucinations without blacklisting real phrases

## Text injection

Uses `pyperclip.copy(" " + text)` then `pyautogui.hotkey("shift", "insert")`.

**Why Shift+Insert instead of Ctrl+V:** Ctrl+V fails in terminals (VS Code terminal, Windows Terminal). Shift+Insert is the universal VT100 paste key that works in both terminals AND regular apps.

**Why clipboard paste instead of SendInput char-by-char:** SendInput character injection is slow and creates gaps/spaces. Clipboard paste is instant regardless of text length.

## Things we tried that didn't work / were reverted

- **RegisterHotKey (ctypes)** for hotkeys — message loop threading was unreliable; replaced with pynput.GlobalHotKeys
- **keyboard library** (`keyboard.add_hotkey`) — unreliable with suppress=True; replaced with pynput
- **Energy VAD at 600ms or less** — mid-sentence pauses split phrases; keep at 1s (10 blocks)
- **beam_size=1 (greedy)** — noticeably worse accuracy; keep at 5
- **vad_filter=False** — Whisper hallucinated "Thank you." on trailing silence; keep it on
- **Content-based hallucination filter** ("thank you" → blocked) — too aggressive, prevents real phrases; use no_speech_prob instead
- **SendInput char-by-char injection** — slow, creates visible gaps between words; replaced with clipboard paste
- **Ctrl+V** for paste — doesn't work in VS Code terminal; replaced with Shift+Insert
- **Ctrl+Shift+V** for terminal detection — detection by window title was unreliable; Shift+Insert is universal
- **SaveForegroundWindow + SetForegroundWindow before paste** — broke everything; reverted
- **Async clipboard restore (background thread)** — accuracy degraded, no speed benefit; reverted
- **Removing injector sleeps** — apps didn't process paste in time; keep the 50ms + 100ms delays
- **Push-to-talk mode** — implemented but no perceptible speed improvement over toggle; removed

## Model storage

Model files live at `%APPDATA%\MurmurAI\models\`. The `is_ready()` check looks for:
1. A `.model_ready` marker file
2. At least one `*.bin` file in the directory

The marker alone isn't enough — it can be created by test mocks. Always check for actual bin files.

## SSL / corporate proxy

If HuggingFace model download fails with SSL errors (common on corporate networks), `model_manager.py` calls `_patch_ssl()` which uses `huggingface_hub.utils._http.set_client_factory` to configure an httpx client with `verify=False`.

## Settings

`%APPDATA%\MurmurAI\settings.json`:
```json
{
  "hotkey": "ctrl+shift+space",
  "language": "en",
  "start_on_login": false
}
```

Hotkey format: lowercase, `+` separated, e.g. `ctrl+shift+space`, `ctrl+f1`.

## Spec and plan docs

- Design spec: `docs/superpowers/specs/2026-05-31-murmurai-design.md`
- Implementation plan: `docs/superpowers/plans/2026-05-31-murmurai.md`
