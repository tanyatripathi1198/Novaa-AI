from __future__ import annotations
import customtkinter as ctk
from typing import Callable, Optional
from controller import State
from hotkey import HotkeyManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_IDLE_COLOR      = "#3a3a5a"
_RECORDING_COLOR = "#e94560"
_TYPING_COLOR    = "#0a84ff"

LANGUAGES = [
    "auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh",
    "ko", "ar", "hi", "nl", "pl", "sv", "tr", "vi", "th", "uk",
    "cs", "ro", "hu", "fi", "da", "no", "id", "ms", "bn", "fa",
]

_STATE_PROPS = {
    State.IDLE:      (_IDLE_COLOR,      "Press to record", "#888888", "🎙"),
    State.RECORDING: (_RECORDING_COLOR, "Recording...",    "#e94560", "🎙"),
    State.TYPING:    (_TYPING_COLOR,    "Typing...",       "#0a84ff", "⌨️"),
}


class MurmurWindow(ctk.CTk):
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_settings_save: Callable[[str, str, bool], None],
        start_on_login: bool = False,
    ) -> None:
        super().__init__()
        self._on_toggle        = on_toggle
        self._on_settings_save = on_settings_save
        self._current_hotkey   = "ctrl+shift+space"
        self._current_language = "auto"
        self._current_login    = start_on_login
        self._setup_window()
        self._show_main()

    # ------------------------------------------------------------------ window

    def _setup_window(self) -> None:
        self.title("MurmurAI")
        self.geometry("240x290")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    # ----------------------------------------------------------- main card view

    def _show_main(self) -> None:
        for w in self.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self, text="MURMURAI",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#888888",
        ).pack(pady=(22, 0))

        self._mic_btn = ctk.CTkButton(
            self, text="🎙", width=68, height=68,
            corner_radius=34, font=ctk.CTkFont(size=28),
            fg_color=_IDLE_COLOR, hover_color="#4a4a7a",
            command=self._on_toggle,
        )
        self._mic_btn.pack(pady=18)

        self._status_lbl = ctk.CTkLabel(
            self, text="Press to record",
            font=ctk.CTkFont(size=11), text_color="#888888",
        )
        self._status_lbl.pack()

        self._hint_lbl = ctk.CTkLabel(
            self, text=self._current_hotkey,
            font=ctk.CTkFont(family="Courier", size=10), text_color="#444444",
        )
        self._hint_lbl.pack(pady=6)

        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(side="bottom", fill="x", padx=16, pady=12)

        self._lang_lbl = ctk.CTkLabel(
            bottom, text=self._lang_display(),
            font=ctk.CTkFont(size=10), text_color="#555555",
        )
        self._lang_lbl.pack(side="left")

        ctk.CTkButton(
            bottom, text="⚙", width=28, height=28,
            fg_color="transparent", text_color="#555555",
            hover_color="#2a2a4a", command=self._show_settings,
        ).pack(side="right")

    # ------------------------------------------------------------------ public

    def update_state(self, state: State) -> None:
        if not hasattr(self, "_mic_btn"):
            return
        color, label, text_color, icon = _STATE_PROPS[state]
        self._mic_btn.configure(fg_color=color, text=icon)
        self._status_lbl.configure(text=label, text_color=text_color)

    def update_hotkey_hint(self, combo: str) -> None:
        self._current_hotkey = combo
        if hasattr(self, "_hint_lbl"):
            self._hint_lbl.configure(text=combo)

    def update_language_display(self, language: str) -> None:
        self._current_language = language
        if hasattr(self, "_lang_lbl"):
            self._lang_lbl.configure(text=self._lang_display())

    def _lang_display(self) -> str:
        return f"🌐 {'Auto' if self._current_language == 'auto' else self._current_language.upper()}"

    # --------------------------------------------------------- settings panel (stub — Task 11)

    def _show_settings(self) -> None:
        for w in self.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self, text="SETTINGS",
            font=ctk.CTkFont(size=11, weight="bold"), text_color="#888888",
        ).pack(pady=(20, 0))

        ctk.CTkLabel(self, text="Hotkey", font=ctk.CTkFont(size=10),
                     text_color="#666666").pack(anchor="w", padx=24, pady=(14, 2))
        self._hk_entry = ctk.CTkEntry(self, font=ctk.CTkFont(family="Courier", size=11))
        self._hk_entry.pack(fill="x", padx=24)
        self._hk_entry.insert(0, self._current_hotkey)
        self._hk_entry.bind("<KeyPress>", self._capture_hotkey)

        ctk.CTkLabel(self, text="Language", font=ctk.CTkFont(size=10),
                     text_color="#666666").pack(anchor="w", padx=24, pady=(12, 2))
        self._lang_menu = ctk.CTkOptionMenu(self, values=LANGUAGES)
        self._lang_menu.pack(fill="x", padx=24)
        self._lang_menu.set(self._current_language)

        self._login_var = ctk.BooleanVar(value=self._current_login)
        ctk.CTkSwitch(
            self, text="Start on login", variable=self._login_var,
            font=ctk.CTkFont(size=11),
        ).pack(padx=24, pady=12, anchor="w")

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(side="bottom", fill="x", padx=16, pady=12)
        ctk.CTkButton(row, text="Cancel", fg_color="#333333",
                      command=self._show_main).pack(side="left")
        ctk.CTkButton(row, text="Save",
                      command=self._save_settings).pack(side="right")

    def _capture_hotkey(self, event) -> str:
        mods = []
        if event.state & 0x4:      mods.append("ctrl")
        if event.state & 0x1:      mods.append("shift")
        if event.state & 0x20000:  mods.append("alt")
        skip = {
            "Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R",
            "caps_lock", "num_lock",
        }
        if event.keysym not in skip:
            combo = "+".join(mods + [event.keysym.lower()])
            self._hk_entry.delete(0, "end")
            self._hk_entry.insert(0, combo)
        return "break"

    def _save_settings(self) -> None:
        hotkey   = self._hk_entry.get().strip()
        language = self._lang_menu.get()
        login    = self._login_var.get()
        if not hotkey or not HotkeyManager.is_valid(hotkey):
            self._hk_entry.configure(border_color="#e94560")
            return
        self._current_hotkey   = hotkey
        self._current_language = language
        self._current_login    = login
        self._on_settings_save(hotkey, language, login)
        self._show_main()
