import ctypes
import ctypes.wintypes as wintypes

KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP   = 0x0002
INPUT_KEYBOARD    = 1


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         wintypes.WORD),
        ("wScan",       wintypes.WORD),
        ("dwFlags",     wintypes.DWORD),
        ("time",        wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("ki",   _KEYBDINPUT),
        ("_pad", ctypes.c_byte * 32),   # pad to MOUSEINPUT size on 64-bit
    ]


class _INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_u",   _INPUTunion),
    ]


try:
    _sendinput = ctypes.windll.user32.SendInput
    _sendinput.argtypes = [wintypes.UINT, ctypes.POINTER(_INPUT), ctypes.c_int]
    _sendinput.restype  = wintypes.UINT
except AttributeError:
    _sendinput = None   # non-Windows / test environment


class TextInjector:
    def type_text(self, text: str) -> None:
        for ch in text:
            self._send(ord(ch))

    def _send(self, code: int) -> None:
        if _sendinput is None:
            return
        pair = (_INPUT * 2)()
        for i, flags in enumerate(
            [KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP]
        ):
            pair[i].type        = INPUT_KEYBOARD
            pair[i]._u.ki.wVk   = 0
            pair[i]._u.ki.wScan = code
            pair[i]._u.ki.dwFlags = flags
        _sendinput(2, pair, ctypes.sizeof(_INPUT))
