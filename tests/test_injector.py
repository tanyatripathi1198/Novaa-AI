import pytest
from unittest.mock import patch, MagicMock


def test_type_text_copies_to_clipboard_and_pastes():
    with patch("injector.pyperclip") as mock_clip, \
         patch("injector.pyautogui") as mock_gui, \
         patch("injector.time"):
        mock_clip.paste.return_value = "original"
        from injector import TextInjector
        TextInjector().type_text("hello")
    mock_clip.copy.assert_any_call(" hello")
    mock_gui.hotkey.assert_called_once_with("ctrl", "v")


def test_type_text_restores_clipboard_after_paste():
    with patch("injector.pyperclip") as mock_clip, \
         patch("injector.pyautogui"), \
         patch("injector.time"):
        mock_clip.paste.return_value = "saved"
        from injector import TextInjector
        TextInjector().type_text("hello")
    # Last copy call should restore original clipboard
    last_copy = mock_clip.copy.call_args_list[-1]
    assert last_copy.args[0] == "saved"


def test_type_text_empty_makes_no_calls():
    with patch("injector.pyperclip") as mock_clip, \
         patch("injector.pyautogui") as mock_gui, \
         patch("injector.time"):
        from injector import TextInjector
        TextInjector().type_text("")
    mock_gui.hotkey.assert_not_called()
    mock_clip.copy.assert_not_called()


def test_type_text_adds_leading_space():
    with patch("injector.pyperclip") as mock_clip, \
         patch("injector.pyautogui"), \
         patch("injector.time"):
        mock_clip.paste.return_value = ""
        from injector import TextInjector
        TextInjector().type_text("world")
    copied_text = mock_clip.copy.call_args_list[0].args[0]
    assert copied_text.startswith(" ")
