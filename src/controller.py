import queue
import threading
from enum import Enum
from typing import Callable, Optional
import numpy as np


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
        self._lock        = threading.RLock()
        self._q: queue.Queue = queue.Queue()
        self._worker: Optional[threading.Thread] = None

    @property
    def state(self) -> State:
        return self._state

    def toggle(self) -> None:
        with self._lock:
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
        try:
            self._audio.stop()   # fires chunk_callback for any buffered speech
        except Exception:
            pass
        self._set_state(State.TYPING)
        self._q.put(None)        # sentinel — ends transcription worker
        worker_snapshot = self._worker
        threading.Thread(target=self._await_idle, args=(worker_snapshot,), daemon=True).start()

    def _transcribe_loop(self) -> None:
        while True:
            chunk = self._q.get()
            if chunk is None:
                return
            text = self._transcriber.transcribe(chunk)
            if text:
                self._injector.type_text(text + " ")

    def _await_idle(self, worker: Optional[threading.Thread]) -> None:
        if worker:
            worker.join(timeout=15)
        self._set_state(State.IDLE)

    def _set_state(self, state: State) -> None:
        with self._lock:
            self._state = state
        if self._on_state:
            self._on_state(state)
