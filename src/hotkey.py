from __future__ import annotations
from typing import Callable, Optional
from pynput import keyboard as _kb

_SPECIAL = {
    "ctrl", "shift", "alt", "win", "space",
    *{f"f{i}" for i in range(1, 13)},
}


def _hotkey_key_groups(combo: str) -> list:
    """Parse 'ctrl+shift+space' into a flat list of canonical pynput key objects."""
    _KEY = {
        "ctrl":  [_kb.Key.ctrl_l, _kb.Key.ctrl_r],
        "shift": [_kb.Key.shift_l, _kb.Key.shift_r],
        "alt":   [_kb.Key.alt_l, _kb.Key.alt_r],
        "win":   [_kb.Key.cmd, _kb.Key.cmd_l, _kb.Key.cmd_r],
        "space": [_kb.Key.space],
        **{f"f{i}": [getattr(_kb.Key, f"f{i}")] for i in range(1, 13)},
        **{chr(c): [_kb.KeyCode.from_char(chr(c))] for c in range(ord("a"), ord("z") + 1)},
    }
    result = []
    for part in combo.lower().split("+"):
        part = part.strip()
        if part in _KEY:
            result.extend(_KEY[part])
    return result


def _to_pynput(combo: str) -> str:
    """Convert 'ctrl+shift+space' to '<ctrl>+<shift>+<space>'."""
    parts = []
    for p in combo.lower().split("+"):
        p = p.strip()
        parts.append(f"<{p}>" if p in _SPECIAL else p)
    return "+".join(parts)


class HotkeyManager:
    def __init__(self) -> None:
        self._listener: Optional[_kb.GlobalHotKeys] = None
        self._current: Optional[str] = None

    def register(self, combo: str, callback: Callable[[], None]) -> None:
        self.unregister()
        pynput_combo = _to_pynput(combo)
        try:
            self._listener = _kb.GlobalHotKeys({pynput_combo: callback})
            self._listener.start()
            self._current = combo
        except Exception:
            self._listener = None

    def register_push_to_talk(
        self,
        combo: str,
        on_press: Callable[[], None],
        on_release: Callable[[], None],
    ) -> None:
        self.unregister()
        key_groups = _hotkey_key_groups(combo)
        _pressed: set = set()
        _active = [False]   # use list for nonlocal mutation in nested fns

        def _on_press(key):
            _pressed.add(key)
            if not _active[0] and all(
                any(k == p for p in _pressed) for k in key_groups
            ):
                _active[0] = True
                on_press()

        def _on_release(key):
            is_combo = any(key == k for k in key_groups)
            _pressed.discard(key)
            if _active[0] and is_combo:
                _active[0] = False
                on_release()

        self._listener = _kb.Listener(on_press=_on_press, on_release=_on_release)
        self._listener.start()
        self._current = combo

    def unregister(self) -> None:
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._current = None

    @staticmethod
    def is_valid(combo: str) -> bool:
        try:
            _kb.HotKey.parse(_to_pynput(combo))
            return True
        except Exception:
            return False
