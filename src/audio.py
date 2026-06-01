import numpy as np
import sounddevice as sd
import warnings
from typing import Callable, Optional

SAMPLE_RATE = 16_000
_BLOCK_SIZE = int(SAMPLE_RATE * 0.1)        # 100ms device blocks
_SILENCE_THRESHOLD = 0.008                   # RMS below this = silence (tuned to mic noise floor ~0.005)
_SILENCE_BLOCKS_TO_END = 6                  # 600ms of silence ends a phrase
_MIN_SPEECH_BLOCKS = 3                       # 300ms minimum for a valid phrase
_PRE_BUFFER_BLOCKS = 3                       # 300ms pre-buffer to catch consonant onsets before VAD triggers


class AudioCapture:
    def __init__(self) -> None:
        self._stream: Optional[sd.InputStream] = None
        self._chunk_cb: Optional[Callable] = None
        self._speech_buf: list = []
        self._pre_buf: list = []
        self._silence_count: int = 0
        self._speaking: bool = False

    def start(self, chunk_callback: Callable[[np.ndarray], None]) -> None:
        if self._stream is not None:
            raise RuntimeError("AudioCapture is already running; call stop() first")
        self._chunk_cb = chunk_callback
        self._speech_buf = []
        self._pre_buf = []
        self._silence_count = 0
        self._speaking = False
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
        # Flush any buffered speech that hasn't ended with silence yet
        if self._speaking and len(self._speech_buf) >= _MIN_SPEECH_BLOCKS:
            phrase = np.concatenate(self._speech_buf).astype(np.float32)
            if self._chunk_cb:
                self._chunk_cb(phrase)
        self._speech_buf = []
        self._pre_buf = []
        self._silence_count = 0
        self._speaking = False
        return np.zeros(0, dtype=np.float32)

    def _on_audio(self, indata, frames, time, status) -> None:
        if status:
            warnings.warn(f"AudioCapture stream status: {status}", RuntimeWarning)
        block = indata[:, 0].copy()
        rms = float(np.sqrt(np.mean(block ** 2)))
        is_speech = rms > _SILENCE_THRESHOLD

        if is_speech:
            if not self._speaking:
                # Prepend pre-buffer so word onsets aren't clipped
                self._speech_buf = list(self._pre_buf)
                self._pre_buf = []
            self._speech_buf.append(block)
            self._silence_count = 0
            self._speaking = True
        elif self._speaking:
            self._speech_buf.append(block)   # include trailing silence
            self._silence_count += 1
            if self._silence_count >= _SILENCE_BLOCKS_TO_END:
                if len(self._speech_buf) >= _MIN_SPEECH_BLOCKS and self._chunk_cb:
                    phrase = np.concatenate(self._speech_buf).astype(np.float32)
                    self._chunk_cb(phrase)
                self._speech_buf = []
                self._silence_count = 0
                self._speaking = False
        else:
            # Not speaking — maintain rolling pre-buffer
            self._pre_buf.append(block)
            if len(self._pre_buf) > _PRE_BUFFER_BLOCKS:
                self._pre_buf.pop(0)
