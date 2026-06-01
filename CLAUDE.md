# Novaa AI — Claude Code Guide

## Project overview

Windows voice-to-text dictation app. Press a hotkey (or say "Hey Nova") → speak → text is pasted wherever the cursor is. All transcription runs locally via Whisper (faster-whisper). No cloud, no API key.

## Running the app

```bash
python src/main.py
```

First launch: downloads Whisper small model (~500MB) to `%APPDATA%\NovaaAI\models\`. Subsequent launches skip the download and use the local snapshot path directly (bypasses HuggingFace network calls).

## Running tests

```bash
python -m pytest tests/ -v        # all 48 tests
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
  tray.py          — pystray system tray icon with N-logo (state-aware colour)
  ui.py            — CustomTkinter elegant card window + settings panel (NovaaAIWindow)
  settings.py      — JSON settings load/save (%APPDATA%\NovaaAI\settings.json)
  model_manager.py — model download guard (marker file + .bin check)
  wake_word.py     — OpenWakeWord wake word listener (Hey Nova)
  sounds.py        — winsound beep effects (start/stop recording)
  icon_maker.py    — generates N-logo .ico file for window/taskbar icon
tests/
  test_*.py        — 48 unit tests per module, all hardware mocked
```

## Architecture

Single Python process. Four layers:

1. **UI** (main thread) — CustomTkinter `NovaaAIWindow` + pystray tray
2. **Controller** (main thread) — state machine, RLock for thread safety
3. **Audio + Transcription** (background thread) — sounddevice → VAD → faster-whisper
4. **Text injection** — pyperclip + Shift+Insert paste
5. **Wake word** (daemon thread, optional) — OpenWakeWord background mic stream

UI updates always go through `window.after(0, ...)` to stay on the main thread.

## Key tuning constants

`src/audio.py`:
- `_SILENCE_THRESHOLD = 0.008` — mic noise floor on this machine peaks at 0.0055 RMS; threshold is safely above that
- `_SILENCE_BLOCKS_TO_END = 5` — **500ms** of silence ends a phrase; was 10 (1s) but reduced to cut latency
- `_MIN_SPEECH_BLOCKS = 5` — 500ms minimum actual speech; prevents noise bursts from triggering transcription

`src/transcriber.py`:
- `beam_size=5` — best accuracy for clear speech on CPU; reducing improves speed but hurts accuracy
- `vad_filter=True, min_silence_duration_ms=500` — strips trailing silence from phrases, prevents Whisper hallucinations
- `condition_on_previous_text=False` — each phrase is independent, prevents repetition artifacts
- Confidence filter: `no_speech_prob < 0.6` — Whisper's own signal; filters hallucinations without blacklisting real phrases
- **Model loaded via direct snapshot path** (`_local_model_path()`) to avoid HuggingFace 403/SSL on corporate networks

`src/controller.py`:
- `wake_start()` uses `silence_blocks=15` (1.5s) — longer than hotkey (5 blocks) to tolerate thinking pauses
- Auto-stop via `on_phrase_end` callback — fires `_end_recording()` in wake mode only

## Transcriber warm-up

At startup, after `transcriber.load()`, a silent dummy transcription is run:
```python
transcriber.transcribe(np.zeros(16_000, dtype=np.float32))
```
Without this, the first real transcription takes ~700ms extra (XNNPACK delegate cold start). With it, all phrases take ~70ms consistently.

## Text injection

Uses `pyperclip.copy(" " + text)` then `pyautogui.hotkey("shift", "insert")`.
Post-paste sleep: `time.sleep(0.05)` — minimal wait for target app to process.
Clipboard is restored to original content after paste (runs synchronously in injector).

**Why Shift+Insert instead of Ctrl+V:** Ctrl+V fails in terminals (VS Code terminal, Windows Terminal). Shift+Insert is the universal VT100 paste key that works in both terminals AND regular apps.

## Sound effects

`src/sounds.py` uses `winsound.Beep` in daemon threads:
- Start recording: two ascending beeps (880Hz + 1100Hz, 80+100ms)
- Stop recording: one low beep (550Hz, 150ms)

## Wake word

`src/wake_word.py` — `WakeWordListener` class:
- Uses OpenWakeWord with TFLite inference (`ai-edge-litert` package)
- Model: `%APPDATA%\NovaaAI\Hey_Nova_20260328_194345.tflite`
- Audio: separate sounddevice stream at 16kHz int16, 1280-sample chunks
- Detection threshold: 0.5
- Loads in background thread after window appears (avoids 10-15s startup delay)
- Tested model: "Hey Nova" scores 0.99; "Hey Pooky" model was ~0.0002 (bad training)

## Icon system

`src/icon_maker.py` — generates `%APPDATA%\NovaaAI\novaaai.ico`:
- Multi-size ICO (16, 32, 48, 64, 128, 256px)
- Design: dark rounded square + hand-drawn N in white lines
- Set via `window.iconbitmap(ico_path)` in main.py

Taskbar grouping fixed via:
```python
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("NovaaAI.VoiceToText")
```

## UI design

`NovaaAIWindow` (elegant theme):
- Background: `#0b0b0f`
- Top bar: white N logo box + "NOVAA AI" thin caps label
- Mic button: 72px circle, state-aware border (subtle white / red-tinted / blue-tinted)
- Status: thin 10px text, letter-spaced
- Settings: frosted inputs, gradient Save button (`#eeeeee` bg, `#0b0b0f` text)
- Window expands to 370px when settings open, restores to 300px on close

**Note:** CustomTkinter does NOT support 8-digit hex colors (RRGGBBAA). All alpha-channel colors must be pre-blended against `#0b0b0f` before use.

## Things we tried that didn't work / were reverted

- **RegisterHotKey (ctypes)** for hotkeys — message loop threading was unreliable; replaced with pynput.GlobalHotKeys
- **keyboard library** (`keyboard.add_hotkey`) — unreliable with suppress=True; replaced with pynput
- **Energy VAD at 1s or more** — was fine for accuracy but adds to latency; reduced to 500ms
- **beam_size=1 (greedy)** — noticeably worse accuracy; keep at 5
- **vad_filter=False** — Whisper hallucinated "Thank you." on trailing silence; keep it on
- **Content-based hallucination filter** ("thank you" → blocked) — too aggressive, prevents real phrases; use no_speech_prob instead
- **SendInput char-by-char injection** — slow, creates visible gaps between words; replaced with clipboard paste
- **Ctrl+V** for paste — doesn't work in VS Code terminal; replaced with Shift+Insert
- **Ctrl+Shift+V for terminal detection** — detection by window title was unreliable; Shift+Insert is universal
- **SaveForegroundWindow + SetForegroundWindow before paste** — broke everything; reverted
- **Async clipboard restore** — no benefit; reverted to synchronous
- **Push-to-talk mode** — implemented but no perceptible speed improvement over toggle; removed
- **Early phrase fire at 200ms** — caused chunked text output (typing mid-sentence); user preferred single-shot; reverted
- **Picovoice Porcupine** for wake word — moved to enterprise/paid tier; switched to OpenWakeWord (fully free)
- **Hey Pooky wake word model** — very poor quality (max score 0.0002); switched to Hey Nova model (0.99 score)

## Model storage

Model files live at `%APPDATA%\NovaaAI\models\`. The `is_ready()` check looks for:
1. A `.model_ready` marker file
2. At least one `*.bin` file in the directory

The marker alone isn't enough — it can be created by test mocks. Always check for actual bin files.

Transcriber uses `_local_model_path()` to find the exact snapshot directory from `refs/main`, bypassing HuggingFace network checks entirely.

## SSL / corporate proxy

Corporate networks block HuggingFace with 403. The transcriber uses `local_files_only` via direct snapshot path. For model downloads, `model_manager._patch_ssl()` configures httpx with `verify=False` via `set_client_factory`.

## Settings

`%APPDATA%\NovaaAI\settings.json`:
```json
{
  "hotkey": "ctrl+shift+space",
  "language": "en",
  "start_on_login": false,
  "wake_word_enabled": false
}
```

Hotkey format: lowercase, `+` separated, e.g. `ctrl+shift+space`, `ctrl+f1`.

## Spec and plan docs

- Design spec: `docs/superpowers/specs/2026-05-31-novaaai-design.md`
- Implementation plan: `docs/superpowers/plans/2026-05-31-novaaai.md`
- Wake word spec: `docs/superpowers/specs/2026-06-01-wake-word-design.md`
- Wake word plan: `docs/superpowers/plans/2026-06-01-wake-word.md`
