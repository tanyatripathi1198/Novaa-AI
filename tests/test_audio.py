import numpy as np
import pytest
from unittest.mock import patch, MagicMock


def _feed(cap, mock_sd, n_blocks, block_ms=100):
    """Feed n_blocks of audio through the sounddevice callback."""
    from audio import SAMPLE_RATE
    cb = mock_sd.InputStream.call_args.kwargs["callback"]
    block = np.zeros((int(SAMPLE_RATE * block_ms / 1000), 1), dtype=np.float32)
    for _ in range(n_blocks):
        cb(block, None, None, None)


def test_one_second_of_audio_fires_one_chunk():
    received = []
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=received.append)
        _feed(cap, mock_sd, n_blocks=10)   # 10 × 100ms = 1s
    assert len(received) == 1
    from audio import SAMPLE_RATE
    assert len(received[0]) == SAMPLE_RATE


def test_partial_second_does_not_fire_chunk():
    received = []
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=received.append)
        _feed(cap, mock_sd, n_blocks=5)   # 0.5s — below threshold
    assert len(received) == 0


def test_stop_returns_remainder():
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        from audio import AudioCapture, SAMPLE_RATE
        cap = AudioCapture()
        cap.start(chunk_callback=lambda _: None)
        _feed(cap, mock_sd, n_blocks=5)   # 0.5s remainder
        remainder = cap.stop()
    assert len(remainder) == int(SAMPLE_RATE * 0.5)


def test_stop_closes_stream():
    with patch("audio.sd") as mock_sd:
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=lambda _: None)
        cap.stop()
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()
