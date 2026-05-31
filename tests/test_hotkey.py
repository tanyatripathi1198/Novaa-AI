import pytest
from unittest.mock import patch, MagicMock


def test_register_calls_add_hotkey():
    with patch("hotkey.keyboard") as mock_kb:
        from hotkey import HotkeyManager
        cb = MagicMock()
        HotkeyManager().register("ctrl+shift+space", cb)
    mock_kb.add_hotkey.assert_called_once_with("ctrl+shift+space", cb, suppress=True)


def test_register_removes_previous_before_adding():
    with patch("hotkey.keyboard") as mock_kb:
        from hotkey import HotkeyManager
        cb = MagicMock()
        mgr = HotkeyManager()
        mgr.register("ctrl+shift+space", cb)
        mgr.register("ctrl+f1", cb)
    mock_kb.remove_hotkey.assert_called_once_with("ctrl+shift+space")
    assert mock_kb.add_hotkey.call_count == 2


def test_unregister_when_nothing_registered_does_not_raise():
    with patch("hotkey.keyboard"):
        from hotkey import HotkeyManager
        HotkeyManager().unregister()   # must not raise


def test_is_valid_true_for_parseable_combo():
    with patch("hotkey.keyboard") as mock_kb:
        mock_kb.parse_hotkey.return_value = MagicMock()
        from hotkey import HotkeyManager
        assert HotkeyManager.is_valid("ctrl+shift+space") is True


def test_is_valid_false_for_unparseable_combo():
    with patch("hotkey.keyboard") as mock_kb:
        mock_kb.parse_hotkey.side_effect = Exception("bad")
        from hotkey import HotkeyManager
        assert HotkeyManager.is_valid("garbage") is False
