import pytest
import threading
from unittest.mock import patch, MagicMock, call


def test_is_valid_space():
    from hotkey import HotkeyManager
    assert HotkeyManager.is_valid("ctrl+shift+space") is True


def test_is_valid_function_key():
    from hotkey import HotkeyManager
    assert HotkeyManager.is_valid("ctrl+alt+f5") is True


def test_is_valid_unknown_key_returns_false():
    from hotkey import HotkeyManager
    assert HotkeyManager.is_valid("ctrl+shift+xyz_bad") is False


def test_register_starts_thread():
    """register() should start a background thread."""
    with patch("hotkey.ctypes.windll.user32.RegisterHotKey", return_value=True), \
         patch("hotkey.ctypes.windll.user32.GetMessageW", return_value=0), \
         patch("hotkey.ctypes.windll.user32.UnregisterHotKey"), \
         patch("hotkey.ctypes.windll.kernel32.GetCurrentThreadId", return_value=1234):
        from hotkey import HotkeyManager
        mgr = HotkeyManager()
        mgr.register("ctrl+shift+space", MagicMock())
        # Thread was created
        assert mgr._thread is not None


def test_register_skips_unknown_combo():
    """register() with an unrecognised key should not start a thread."""
    from hotkey import HotkeyManager
    mgr = HotkeyManager()
    mgr.register("ctrl+shift+xyz_bad", MagicMock())
    assert mgr._thread is None


def test_unregister_when_nothing_registered_does_not_raise():
    from hotkey import HotkeyManager
    HotkeyManager().unregister()   # must not raise
