import numpy as np
import sounddevice as sd
from typing import Callable, Optional

SAMPLE_RATE = 16_000
CHUNK_SECONDS = 1.0
_BLOCK_SIZE = int(SAMPLE_RATE * 0.1)   # 100ms blocks from device


class AudioCapture:
    def __init__(self) -> None:
        self._stream: Optional[sd.InputStream] = None
        self._buffer = np.array([], dtype=np.float32)
        self._chunk_cb: Optional[Callable] = None

    def start(self, chunk_callback: Callable[[np.ndarray], None]) -> None:
        self._chunk_cb = chunk_callback
        self._buffer = np.array([], dtype=np.float32)
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            blocksize=_BLOCK_SIZE,
            callback=self._on_audio,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        leftover = self._buffer.copy()
        self._buffer = np.array([], dtype=np.float32)
        return leftover

    def _on_audio(self, indata, frames, time, status) -> None:
        chunk_size = int(SAMPLE_RATE * CHUNK_SECONDS)
        self._buffer = np.concatenate([self._buffer, indata[:, 0]])
        while len(self._buffer) >= chunk_size:
            chunk, self._buffer = (
                self._buffer[:chunk_size],
                self._buffer[chunk_size:],
            )
            if self._chunk_cb:
                self._chunk_cb(chunk)
