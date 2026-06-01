import ctypes
import ctypes.wintypes as wintypes
import threading
from typing import Callable, Optional

WM_HOTKEY = 0x0312
WM_QUIT   = 0x0012
_HOTKEY_ID = 1

_MOD = {
    "ctrl":  0x0002,
    "shift": 0x0004,
    "alt":   0x0001,
    "win":   0x0008,
}

_VK = {
    "space": 0x20,
    **{f"f{i}": 0x6F + i for i in range(1, 13)},   # F1=0x70 … F12=0x7B
    **{chr(c): ord(chr(c).upper()) for c in range(ord("a"), ord("z") + 1)},
}


def _parse(combo: str):
    mods, vk = 0, 0
    for part in combo.lower().split("+"):
        part = part.strip()
        if part in _MOD:
            mods |= _MOD[part]
        elif part in _VK:
            vk = _VK[part]
    return mods, vk


class HotkeyManager:
    def __init__(self) -> None:
        self._thread: Optional[threading.Thread] = None
        self._tid: Optional[int] = None
        self._ready = threading.Event()
        self._current: Optional[str] = None

    def register(self, combo: str, callback: Callable[[], None]) -> None:
        self.unregister()
        mods, vk = _parse(combo)
        if vk == 0:
            return
        self._current = combo
        self._ready.clear()
        self._thread = threading.Thread(
            target=self._loop, args=(mods, vk, callback), daemon=True
        )
        self._thread.start()
        self._ready.wait(timeout=1.0)   # wait for _tid to be set before returning

    def unregister(self) -> None:
        if self._tid is not None:
            ctypes.windll.user32.PostThreadMessageW(self._tid, WM_QUIT, 0, 0)
            if self._thread:
                self._thread.join(timeout=2)
        self._tid = None
        self._thread = None
        self._current = None

    def _loop(self, mods: int, vk: int, callback: Callable) -> None:
        self._tid = ctypes.windll.kernel32.GetCurrentThreadId()
        self._ready.set()
        if not ctypes.windll.user32.RegisterHotKey(None, _HOTKEY_ID, mods, vk):
            return
        msg = wintypes.MSG()
        while True:
            result = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if result == 0 or result == -1:
                break
            if msg.message == WM_HOTKEY:
                callback()
        ctypes.windll.user32.UnregisterHotKey(None, _HOTKEY_ID)

    @staticmethod
    def is_valid(combo: str) -> bool:
        _, vk = _parse(combo)
        return vk != 0
