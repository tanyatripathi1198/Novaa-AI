import numpy as np
import pytest
from unittest.mock import MagicMock, patch


def _make_segment(text):
    s = MagicMock()
    s.text = text
    return s


def _loaded_transcriber(language="auto", mock_model=None):
    mock_model = mock_model or MagicMock()
    mock_model.transcribe.return_value = ([], MagicMock())
    with patch("transcriber.WhisperModel", return_value=mock_model):
        from transcriber import Transcriber
        t = Transcriber(language=language, _model_cls=mock_model.__class__)
        # bypass real load by directly assigning
        t._model = mock_model
    return t, mock_model


def test_transcribe_joins_segments():
    t, mock_model = _loaded_transcriber()
    mock_model.transcribe.return_value = (
        [_make_segment("Hello "), _make_segment("world")], MagicMock()
    )
    result = t.transcribe(np.zeros(16_000, dtype=np.float32))
    assert result == "Hello world"


def test_transcribe_returns_empty_on_no_segments():
    t, mock_model = _loaded_transcriber()
    mock_model.transcribe.return_value = ([], MagicMock())
    assert t.transcribe(np.zeros(16_000, dtype=np.float32)) == ""


def test_transcribe_raises_if_not_loaded():
    from transcriber import Transcriber
    t = Transcriber()
    with pytest.raises(RuntimeError, match="load\\(\\)"):
        t.transcribe(np.zeros(16_000, dtype=np.float32))


def test_explicit_language_passed_to_model():
    t, mock_model = _loaded_transcriber(language="fr")
    mock_model.transcribe.return_value = ([], MagicMock())
    t.transcribe(np.zeros(16_000, dtype=np.float32))
    assert mock_model.transcribe.call_args.kwargs["language"] == "fr"


def test_auto_language_passes_none_to_model():
    t, mock_model = _loaded_transcriber(language="auto")
    mock_model.transcribe.return_value = ([], MagicMock())
    t.set_language("auto")
    t.transcribe(np.zeros(16_000, dtype=np.float32))
    assert mock_model.transcribe.call_args.kwargs["language"] is None


def test_set_language_updates_future_calls():
    t, mock_model = _loaded_transcriber(language="auto")
    mock_model.transcribe.return_value = ([], MagicMock())
    t.set_language("de")
    t.transcribe(np.zeros(16_000, dtype=np.float32))
    assert mock_model.transcribe.call_args.kwargs["language"] == "de"
