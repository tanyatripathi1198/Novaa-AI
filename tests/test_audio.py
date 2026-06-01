import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from audio import _BLOCK_MS, _SILENCE_BLOCKS_TO_END, _MIN_SPEECH_BLOCKS, TARGET_RATE

_BLOCK_SIZE = int(TARGET_RATE * _BLOCK_MS / 1000)   # 100ms at 16kHz


def _start_cap(received):
    """Start AudioCapture with mocked sounddevice at native_rate == TARGET_RATE."""
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        mock_sd.query_devices.return_value = {"default_samplerate": TARGET_RATE}
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=received.append)
        cb = mock_sd.InputStream.call_args.kwargs["callback"]
    return cap, cb


def _feed_speech(cb, n_blocks):
    block = np.ones((_BLOCK_SIZE, 1), dtype=np.float32) * 0.5
    for _ in range(n_blocks):
        cb(block, None, None, None)


def _feed_silence(cb, n_blocks):
    block = np.zeros((_BLOCK_SIZE, 1), dtype=np.float32)
    for _ in range(n_blocks):
        cb(block, None, None, None)


def test_speech_followed_by_silence_fires_callback():
    received = []
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        mock_sd.query_devices.return_value = {"default_samplerate": TARGET_RATE}
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=received.append)
        cb = mock_sd.InputStream.call_args.kwargs["callback"]
        _feed_speech(cb, _MIN_SPEECH_BLOCKS + 1)
        _feed_silence(cb, _SILENCE_BLOCKS_TO_END)
    assert len(received) == 1


def test_silence_only_never_fires_callback():
    received = []
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        mock_sd.query_devices.return_value = {"default_samplerate": TARGET_RATE}
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=received.append)
        cb = mock_sd.InputStream.call_args.kwargs["callback"]
        _feed_silence(cb, 20)
    assert len(received) == 0


def test_stop_flushes_buffered_speech():
    received = []
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        mock_sd.query_devices.return_value = {"default_samplerate": TARGET_RATE}
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=received.append)
        cb = mock_sd.InputStream.call_args.kwargs["callback"]
        _feed_speech(cb, _MIN_SPEECH_BLOCKS + 2)
        cap.stop()
    assert len(received) == 1


def test_stop_returns_empty_array_and_closes_stream():
    with patch("audio.sd") as mock_sd:
        mock_stream = MagicMock()
        mock_sd.InputStream.return_value = mock_stream
        mock_sd.query_devices.return_value = {"default_samplerate": TARGET_RATE}
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=lambda _: None)
        result = cap.stop()
    assert len(result) == 0
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()


def test_custom_silence_blocks_used_in_vad():
    received = []
    with patch("audio.sd") as mock_sd:
        mock_sd.InputStream.return_value = MagicMock()
        mock_sd.query_devices.return_value = {"default_samplerate": TARGET_RATE}
        from audio import AudioCapture
        cap = AudioCapture()
        cap.start(chunk_callback=received.append, silence_blocks=3)
        cb = mock_sd.InputStream.call_args.kwargs["callback"]
        _feed_speech(cb, _MIN_SPEECH_BLOCKS + 1)
        _feed_silence(cb, 3)
    assert len(received) == 1
