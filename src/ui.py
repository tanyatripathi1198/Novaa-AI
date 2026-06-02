from __future__ import annotations
import customtkinter as ctk
from typing import Callable, Optional
from controller import State
from hotkey import HotkeyManager

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

LANGUAGES = [
    "auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "zh",
    "ko", "ar", "hi", "nl", "pl", "sv", "tr", "vi", "th", "uk",
    "cs", "ro", "hu", "fi", "da", "no", "id", "ms", "bn", "fa",
]

# (btn_bg, btn_border, glow_ring, icon_color, status_text, icon)
_STATE_PROPS = {
    State.IDLE:      ("#141419", "#232327", "#0b0b0f", "#8a8a8d", "PRESS TO RECORD", "🎙"),
    State.RECORDING: ("#200d14", "#5c2030", "#2a0f18", "#ff8090", "RECORDING",       "🎙"),
    State.TYPING:    ("#0d1420", "#1a2e50", "#0d1828", "#7ab0ff", "TYPING",           "⌨️"),
}


class NovaaAIWindow(ctk.CTk):
    def __init__(
        self,
        on_toggle: Callable[[], None],
        on_settings_save: Callable[[str, str, bool, bool], None],
        start_on_login: bool = False,
        wake_word_enabled: bool = False,
    ) -> None:
        super().__init__()
        self._on_toggle        = on_toggle
        self._on_settings_save = on_settings_save
        self._current_hotkey   = "ctrl+shift+space"
        self._current_language = "auto"
        self._current_login    = start_on_login
        self._current_wake     = wake_word_enabled
        self._setup_window()
        self._show_main()

    # ── window ──────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.title("Novaa AI")
        self.geometry("240x265")
        self.resizable(False, False)
        self.configure(fg_color="#0b0b0f")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    # ── main card ───────────────────────────────────────────────────────

    def _show_main(self) -> None:
        self.geometry("240x265")
        for w in self.winfo_children():
            w.destroy()

        # ── top bar (14px padding, 44px height) ──
        bar = ctk.CTkFrame(self, fg_color="#0b0b0f", corner_radius=0, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # Logo box: 22×22 white rounded square with bold N
        logo_box = ctk.CTkFrame(bar, width=22, height=22, fg_color="#ffffff", corner_radius=6)
        logo_box.pack(side="left", padx=(14, 10), pady=11)
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="N", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#0b0b0f").place(relx=0.5, rely=0.5, anchor="center")

        # App name: thin, muted, uppercase — matches mockup letter-spacing feel
        ctk.CTkLabel(bar, text="NOVAA AI",
                     font=ctk.CTkFont(size=9, weight="normal"),
                     text_color="#6d6d6f").pack(side="left", pady=11)

        # 1px separator line
        ctk.CTkFrame(self, height=1, fg_color="#1c1c20", corner_radius=0).pack(fill="x")

        # ── mic button with glow ring (28px top padding, centred) ──
        btn_frame = ctk.CTkFrame(self, fg_color="#0b0b0f", corner_radius=0)
        btn_frame.pack(fill="x", pady=(28, 0))

        # Glow ring: 5px larger than button on each side.
        # In idle it is invisible (same as bg). In recording/typing it becomes
        # a coloured halo that matches the mockup's box-shadow glow effect.
        self._mic_glow = ctk.CTkFrame(
            btn_frame,
            fg_color="#0b0b0f",   # idle = invisible
            corner_radius=41,
            width=82, height=82,
        )
        self._mic_glow.pack(anchor="center")
        self._mic_glow.pack_propagate(False)

        self._mic_btn = ctk.CTkButton(
            self._mic_glow,
            text="🎙", width=72, height=72,
            corner_radius=36,
            font=ctk.CTkFont(size=24),
            fg_color="#141419",
            hover_color="#1e1e28",
            border_width=1,
            border_color="#232327",
            text_color="#8a8a8d",
            command=self._on_toggle,
        )
        self._mic_btn.place(relx=0.5, rely=0.5, anchor="center")

        # ── status: uppercase, letter-spaced feel ──
        self._status_lbl = ctk.CTkLabel(
            self, text="PRESS TO RECORD",
            font=ctk.CTkFont(size=9, weight="normal"),
            text_color="#545457",
        )
        self._status_lbl.pack(pady=(16, 0))

        # ── hotkey: subtle bordered chip (matches mockup exactly) ──
        hk_chip = ctk.CTkFrame(
            self, fg_color="#111115", corner_radius=2,
            border_width=1, border_color="#1c1c20",
        )
        hk_chip.pack(pady=(6, 0))
        self._hint_lbl = ctk.CTkLabel(
            hk_chip, text=self._current_hotkey,
            font=ctk.CTkFont(family="Courier New", size=8),
            text_color="#37373a",
        )
        self._hint_lbl.pack(padx=8, pady=3)

        # ── footer ──
        footer = ctk.CTkFrame(self, fg_color="#0b0b0f", corner_radius=0)
        footer.pack(side="bottom", fill="x", padx=16, pady=12)

        self._lang_lbl = ctk.CTkLabel(
            footer, text=self._lang_display(),
            font=ctk.CTkFont(size=8), text_color="#3c3c3f",
        )
        self._lang_lbl.pack(side="left")

        ctk.CTkButton(
            footer, text="⚙", width=24, height=24,
            fg_color="transparent", hover_color="#141418",
            text_color="#37373a", font=ctk.CTkFont(size=10),
            command=self._show_settings,
        ).pack(side="right")

    # ── public state updates ─────────────────────────────────────────────

    def update_state(self, state: State) -> None:
        if not hasattr(self, "_mic_btn"):
            return
        btn_bg, btn_border, glow_bg, icon_color, label, icon = _STATE_PROPS[state]
        # Update glow ring (halo effect)
        if hasattr(self, "_mic_glow"):
            self._mic_glow.configure(fg_color=glow_bg)
        # Update button
        self._mic_btn.configure(
            fg_color=btn_bg, border_color=btn_border,
            text=icon, text_color=icon_color,
        )
        # Update status + hint
        self._status_lbl.configure(text=label, text_color=icon_color)
        if hasattr(self, "_hint_lbl"):
            self._hint_lbl.configure(
                text_color="#37373a" if state == State.IDLE else icon_color
            )

    def update_hotkey_hint(self, combo: str) -> None:
        self._current_hotkey = combo
        if hasattr(self, "_hint_lbl"):
            self._hint_lbl.configure(text=combo)

    def update_language_display(self, language: str) -> None:
        self._current_language = language
        if hasattr(self, "_lang_lbl"):
            self._lang_lbl.configure(text=self._lang_display())

    def _lang_display(self) -> str:
        return f"🌐 {'auto' if self._current_language == 'auto' else self._current_language}"

    # ── settings panel ───────────────────────────────────────────────────

    def _show_settings(self) -> None:
        self.geometry("240x360")
        for w in self.winfo_children():
            w.destroy()

        # top bar
        bar = ctk.CTkFrame(self, fg_color="#0b0b0f", corner_radius=0, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        logo_box = ctk.CTkFrame(bar, width=22, height=22, fg_color="#ffffff", corner_radius=5)
        logo_box.pack(side="left", padx=(14, 8), pady=11)
        logo_box.pack_propagate(False)
        ctk.CTkLabel(logo_box, text="N", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color="#0b0b0f").place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(bar, text="SETTINGS",
                     font=ctk.CTkFont(size=9), text_color="#3c3c3f").pack(side="left", pady=11)
        sep = ctk.CTkFrame(self, height=1, fg_color="#171719", corner_radius=0)
        sep.pack(fill="x")

        pad = {"padx": 20}

        # Hotkey
        ctk.CTkLabel(self, text="HOTKEY", font=ctk.CTkFont(size=8),
                     text_color="#3c3c3f").pack(anchor="w", pady=(14, 3), **pad)
        self._hk_entry = ctk.CTkEntry(
            self, font=ctk.CTkFont(family="Courier New", size=10),
            fg_color="#111115", border_color="#1c1c20",
            text_color="#6c6c70", height=30,
        )
        self._hk_entry.pack(fill="x", **pad)
        self._hk_entry.insert(0, self._current_hotkey)
        self._hk_entry.bind("<KeyPress>", self._capture_hotkey)

        # Language
        ctk.CTkLabel(self, text="LANGUAGE", font=ctk.CTkFont(size=8),
                     text_color="#3c3c3f").pack(anchor="w", pady=(10, 3), **pad)
        self._lang_menu = ctk.CTkOptionMenu(
            self, values=LANGUAGES, height=30,
            fg_color="#111115", button_color="#191920",
            button_hover_color="#222226",
            text_color="#6c6c70", dropdown_fg_color="#111115",
        )
        self._lang_menu.pack(fill="x", **pad)
        self._lang_menu.set(self._current_language)

        # Toggles
        self._login_var = ctk.BooleanVar(value=self._current_login)
        ctk.CTkSwitch(
            self, text="Start on login",
            font=ctk.CTkFont(size=10), text_color="#4c4c50",
            variable=self._login_var,
            button_color="#6c6c70", button_hover_color="#ababae",
            progress_color="#3c3c3f",
        ).pack(anchor="w", pady=(12, 0), **pad)

        self._wake_var = ctk.BooleanVar(value=self._current_wake)
        ctk.CTkSwitch(
            self, text="Wake word (Hey Nova)",
            font=ctk.CTkFont(size=10), text_color="#4c4c50",
            variable=self._wake_var,
            button_color="#6c6c70", button_hover_color="#ababae",
            progress_color="#3c3c3f",
        ).pack(anchor="w", pady=(8, 0), **pad)

        # Buttons
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(side="bottom", fill="x", padx=16, pady=14)
        ctk.CTkButton(
            row, text="Cancel", height=32,
            fg_color="#141418", hover_color="#1e1e22",
            text_color="#4c4c50", font=ctk.CTkFont(size=10),
            command=self._show_main,
        ).pack(side="left", expand=True, padx=(0, 4))
        ctk.CTkButton(
            row, text="Save", height=32,
            fg_color="#eeeeee", hover_color="#cccccc",
            text_color="#0b0b0f", font=ctk.CTkFont(size=10, weight="bold"),
            command=self._save_settings,
        ).pack(side="right", expand=True, padx=(4, 0))

    def _capture_hotkey(self, event) -> str:
        mods = []
        if event.state & 0x4:      mods.append("ctrl")
        if event.state & 0x1:      mods.append("shift")
        if event.state & 0x20000:  mods.append("alt")
        skip = {"Control_L","Control_R","Shift_L","Shift_R","Alt_L","Alt_R","caps_lock","num_lock"}
        if event.keysym not in skip:
            combo = "+".join(mods + [event.keysym.lower()])
            self._hk_entry.delete(0, "end")
            self._hk_entry.insert(0, combo)
        return "break"

    def _save_settings(self) -> None:
        hotkey   = self._hk_entry.get().strip()
        language = self._lang_menu.get()
        login    = self._login_var.get()
        wake     = self._wake_var.get() if hasattr(self, "_wake_var") else self._current_wake
        if not hotkey or not HotkeyManager.is_valid(hotkey):
            self._hk_entry.configure(border_color="#ff6070")
            return
        self._current_hotkey   = hotkey
        self._current_language = language
        self._current_login    = login
        self._current_wake     = wake
        self._on_settings_save(hotkey, language, login, wake)
        self._show_main()
