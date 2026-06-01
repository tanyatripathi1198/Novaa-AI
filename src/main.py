import sys
import threading
import winreg
from pathlib import Path
from typing import Optional

import customtkinter as ctk

from settings import Settings, load as load_settings, save as save_settings
from model_manager import is_ready, ensure_model
from audio import AudioCapture
from transcriber import Transcriber
from injector import TextInjector
from hotkey import HotkeyManager
from controller import Controller, State
from tray import TrayIcon
from ui import MurmurWindow
from wake_word import WakeWordListener, MODEL_PATH


def _migrate_appdata() -> None:
    """Move %APPDATA%\\MurmurAI -> %APPDATA%\\Pooky on first launch after rename."""
    import shutil
    base = Path(os.environ.get("APPDATA", Path.home()))
    old_dir = base / "MurmurAI"
    new_dir = base / "Pooky"
    if old_dir.exists() and not new_dir.exists():
        try:
            shutil.move(str(old_dir), str(new_dir))
        except Exception:
            pass


def _set_start_on_login(enabled: bool) -> None:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    # When frozen (PyInstaller), sys.executable IS the app.
    # When running from source, we need python + script path.
    if getattr(sys, "frozen", False):
        exe_cmd = sys.executable
    else:
        exe_cmd = f'"{sys.executable}" "{Path(__file__).resolve()}"'
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, "Pooky", 0, winreg.REG_SZ, exe_cmd)
        else:
            try:
                winreg.DeleteValue(key, "Pooky")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except OSError:
        pass


def _handle_download_error(root, exc: Exception) -> None:
    import customtkinter as ctk
    for w in root.winfo_children():
        w.destroy()
    ctk.CTkLabel(
        root,
        text=f"Download failed:\n{exc}\n\nCheck your internet connection and restart.",
        wraplength=260,
        text_color="#e94560",
    ).pack(pady=20)
    ctk.CTkButton(root, text="Quit", command=root.destroy).pack()


def _show_download_screen() -> None:
    """Blocking download screen — runs before the main window."""
    root = ctk.CTk()
    root.title("Pooky — First Run")
    root.geometry("300x160")
    root.resizable(False, False)

    ctk.CTkLabel(root, text="Downloading Whisper model (~500 MB)…",
                 wraplength=260).pack(pady=30)
    bar = ctk.CTkProgressBar(root, mode="indeterminate")
    bar.pack(fill="x", padx=30)
    bar.start()

    def _download():
        try:
            ensure_model()
            root.after(0, root.destroy)
        except Exception as exc:
            root.after(0, lambda e=exc: _handle_download_error(root, e))

    threading.Thread(target=_download, daemon=True).start()
    root.mainloop()


def main() -> None:
    _migrate_appdata()
    if not is_ready():
        _show_download_screen()

    settings = load_settings()

    audio       = AudioCapture()
    transcriber = Transcriber(language=settings.language)
    injector    = TextInjector()
    hotkey_mgr  = HotkeyManager()

    transcriber.load()   # ~1-2s on first call; blocks here intentionally

    # controller is referenced by the lambda before assignment — that is fine
    # because the lambda is only called after controller is created below.
    controller: Controller  # forward declaration for type checkers
    tray: Optional[TrayIcon] = None
    wake_listener: Optional[WakeWordListener] = None

    def _start_wake_listener() -> None:
        nonlocal wake_listener
        if wake_listener:
            wake_listener.stop()
            wake_listener = None
        if not Path(str(MODEL_PATH)).exists():
            return
        try:
            wake_listener = WakeWordListener(
                on_detect=lambda: (
                    controller.wake_start()
                    if controller.state == State.IDLE else None
                ),
            )
            wake_listener.start()
        except Exception:
            wake_listener = None

    def handle_settings_save(hotkey: str, language: str, start_on_login: bool, wake_word_enabled: bool) -> None:
        settings.hotkey             = hotkey
        settings.language           = language
        settings.start_on_login     = start_on_login
        settings.wake_word_enabled  = wake_word_enabled
        save_settings(settings)
        hotkey_mgr.register(hotkey, controller.toggle)
        transcriber.set_language(language)
        window.update_hotkey_hint(hotkey)
        window.update_language_display(language)
        _set_start_on_login(start_on_login)
        if wake_word_enabled:
            _start_wake_listener()
        else:
            if wake_listener:
                wake_listener.stop()

    window = MurmurWindow(
        on_toggle=lambda: controller.toggle(),
        on_settings_save=handle_settings_save,
        start_on_login=settings.start_on_login,
        wake_word_enabled=settings.wake_word_enabled,
    )

    def on_state_change(state: State) -> None:
        window.after(0, lambda s=state: window.update_state(s))
        if tray is not None:
            tray.set_state(state.value)

    controller = Controller(
        audio, transcriber, injector,
        on_state_change=on_state_change,
    )

    def quit_app() -> None:
        hotkey_mgr.unregister()
        if wake_listener:
            wake_listener.stop()
        tray.stop()
        window.after(0, window.destroy)

    tray = TrayIcon(
        on_open=lambda: window.after(0, window.deiconify),
        on_quit=quit_app,
    )
    tray.start()

    hotkey_mgr.register(settings.hotkey, controller.toggle)
    window.update_hotkey_hint(settings.hotkey)
    window.update_language_display(settings.language)

    if settings.wake_word_enabled:
        _start_wake_listener()

    window.mainloop()


if __name__ == "__main__":
    main()
