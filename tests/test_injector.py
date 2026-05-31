import pytest
from unittest.mock import patch, MagicMock, call


def test_type_text_calls_send_once_per_character():
    with patch("injector._sendinput") as mock_send:
        from injector import TextInjector
        TextInjector().type_text("hi")
    assert mock_send.call_count == 2


def test_type_text_empty_string_makes_no_calls():
    with patch("injector._sendinput") as mock_send:
        from injector import TextInjector
        TextInjector().type_text("")
    mock_send.assert_not_called()


def test_type_text_unicode_character():
    with patch("injector._sendinput") as mock_send:
        from injector import TextInjector
        TextInjector().type_text("ñ")
    assert mock_send.call_count == 1
