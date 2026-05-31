import time
import numpy as np
import pytest
from unittest.mock import MagicMock
from controller import Controller, State


def _make(on_state=None):
    audio       = MagicMock()
    transcriber = MagicMock()
    injector    = MagicMock()
    transcriber.transcribe.return_value = "hello"
    audio.stop.return_value = np.zeros(0, dtype=np.float32)
    ctrl = Controller(audio, transcriber, injector, on_state_change=on_state)
    return ctrl, audio, transcriber, injector


def test_initial_state_is_idle():
    ctrl, *_ = _make()
    assert ctrl.state == State.IDLE


def test_toggle_idle_starts_recording():
    ctrl, audio, *_ = _make()
    ctrl.toggle()
    assert ctrl.state == State.RECORDING
    audio.start.assert_called_once()


def test_toggle_recording_stops_audio():
    ctrl, audio, *_ = _make()
    ctrl.toggle()
    ctrl.toggle()
    audio.stop.assert_called_once()


def test_chunk_triggers_transcription_and_injection():
    ctrl, audio, transcriber, injector = _make()
    ctrl.toggle()

    chunk_cb = audio.start.call_args.kwargs["chunk_callback"]
    chunk_cb(np.ones(16_000, dtype=np.float32))

    ctrl.toggle()
    time.sleep(0.3)   # allow worker thread

    transcriber.transcribe.assert_called()
    injector.type_text.assert_called()


def test_empty_transcription_not_injected():
    ctrl, audio, transcriber, injector = _make()
    transcriber.transcribe.return_value = ""
    ctrl.toggle()

    chunk_cb = audio.start.call_args.kwargs["chunk_callback"]
    chunk_cb(np.ones(16_000, dtype=np.float32))
    ctrl.toggle()
    time.sleep(0.3)

    injector.type_text.assert_not_called()


def test_state_transitions_reported_in_order():
    states = []
    ctrl, *_ = _make(on_state=states.append)
    ctrl.toggle()   # → RECORDING
    ctrl.toggle()   # → TYPING → IDLE
    time.sleep(0.3)

    assert states[0] == State.RECORDING
    assert State.TYPING in states
    assert states[-1] == State.IDLE
