import keyboard
from typing import Callable, Optional


class HotkeyManager:
    def __init__(self) -> None:
        self._current: Optional[str] = None

    def register(self, combo: str, callback: Callable[[], None]) -> None:
        self.unregister()
        keyboard.add_hotkey(combo, callback, suppress=True)
        self._current = combo

    def unregister(self) -> None:
        if self._current:
            try:
                keyboard.remove_hotkey(self._current)
            except (KeyError, ValueError):
                pass
            self._current = None

    @staticmethod
    def is_valid(combo: str) -> bool:
        try:
            keyboard.parse_hotkey(combo)
            return True
        except Exception:
            return False
