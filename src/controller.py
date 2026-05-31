import queue
import threading
from enum import Enum
from typing import Callable, Optional
import numpy as np

_MIN_TRAILING_SAMPLES = int(16_000 * 0.3)   # ignore < 300ms trailing buffer


class State(Enum):
    IDLE      = "idle"
    RECORDING = "recording"
    TYPING    = "typing"


class Controller:
    def __init__(
        self,
        audio,
        transcriber,
        injector,
        on_state_change: Optional[Callable[[State], None]] = None,
    ) -> None:
        self._audio       = audio
        self._transcriber = transcriber
        self._injector    = injector
        self._on_state    = on_state_change
        self._state       = State.IDLE
        self._q: queue.Queue = queue.Queue()
        self._worker: Optional[threading.Thread] = None

    @property
    def state(self) -> State:
        return self._state

    def toggle(self) -> None:
        if self._state == State.IDLE:
            self._begin_recording()
        elif self._state == State.RECORDING:
            self._end_recording()

    def _begin_recording(self) -> None:
        self._q = queue.Queue()
        self._worker = threading.Thread(target=self._transcribe_loop, daemon=True)
        self._worker.start()
        self._audio.start(chunk_callback=self._q.put)
        self._set_state(State.RECORDING)

    def _end_recording(self) -> None:
        remainder = self._audio.stop()
        self._set_state(State.TYPING)
        if len(remainder) >= _MIN_TRAILING_SAMPLES:
            self._q.put(remainder)
        self._q.put(None)                          # sentinel — ends worker
        threading.Thread(target=self._await_idle, daemon=True).start()

    def _transcribe_loop(self) -> None:
        while True:
            chunk = self._q.get()
            if chunk is None:
                return
            text = self._transcriber.transcribe(chunk)
            if text:
                self._injector.type_text(text + " ")

    def _await_idle(self) -> None:
        if self._worker:
            self._worker.join(timeout=15)
        self._set_state(State.IDLE)

    def _set_state(self, state: State) -> None:
        self._state = state
        if self._on_state:
            self._on_state(state)
