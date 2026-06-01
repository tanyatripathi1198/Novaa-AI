import math
import numpy as np
import sounddevice as sd
import warnings
from scipy.signal import resample_poly
from typing import Callable, Optional

TARGET_RATE = 16_000                         # Whisper requires 16kHz
_BLOCK_MS = 100                              # process audio in 100ms blocks
_SILENCE_THRESHOLD = 0.008                   # RMS below this = silence
_SILENCE_BLOCKS_TO_END = 10                 # 1s of silence ends a phrase
_MIN_SPEECH_BLOCKS = 5                       # 500ms minimum actual speech
_PRE_BUFFER_BLOCKS = 3                       # 300ms pre-buffer for word onsets


class AudioCapture:
    def __init__(self) -> None:
        self._stream: Optional[sd.InputStream] = None
        self._chunk_cb: Optional[Callable] = None
        self._native_rate: int = TARGET_RATE
        self._speech_buf: list = []
        self._pre_buf: list = []
        self._silence_count: int = 0
        self._speech_count: int = 0
        self._speaking: bool = False

    def start(self, chunk_callback: Callable[[np.ndarray], None]) -> None:
        if self._stream is not None:
            raise RuntimeError("AudioCapture is already running; call stop() first")
        self._chunk_cb = chunk_callback
        self._speech_buf = []
        self._pre_buf = []
        self._silence_count = 0
        self._speech_count = 0
        self._speaking = False

        # Use device's native sample rate for best quality, resample later
        try:
            info = sd.query_devices(kind="input")
            self._native_rate = int(info["default_samplerate"])
        except Exception:
            self._native_rate = TARGET_RATE

        block_size = int(self._native_rate * _BLOCK_MS / 1000)
        self._stream = sd.InputStream(
            samplerate=self._native_rate,
            channels=1,
            dtype="float32",
            blocksize=block_size,
            callback=self._on_audio,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if self._speaking and self._speech_count >= _MIN_SPEECH_BLOCKS:
            phrase = self._build_phrase()
            if self._chunk_cb:
                self._chunk_cb(phrase)
        self._speech_buf = []
        self._pre_buf = []
        self._silence_count = 0
        self._speech_count = 0
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
                self._speech_buf = list(self._pre_buf)
                self._pre_buf = []
                self._speech_count = 0
            self._speech_buf.append(block)
            self._speech_count += 1
            self._silence_count = 0
            self._speaking = True
        elif self._speaking:
            self._speech_buf.append(block)
            self._silence_count += 1
            if self._silence_count >= _SILENCE_BLOCKS_TO_END:
                if self._speech_count >= _MIN_SPEECH_BLOCKS and self._chunk_cb:
                    self._chunk_cb(self._build_phrase())
                self._speech_buf = []
                self._silence_count = 0
                self._speech_count = 0
                self._speaking = False
        else:
            self._pre_buf.append(block)
            if len(self._pre_buf) > _PRE_BUFFER_BLOCKS:
                self._pre_buf.pop(0)

    def _build_phrase(self) -> np.ndarray:
        audio = np.concatenate(self._speech_buf).astype(np.float32)
        if self._native_rate == TARGET_RATE:
            return audio
        # Polyphase resampling: high-quality, no aliasing artifacts
        gcd = math.gcd(TARGET_RATE, self._native_rate)
        return resample_poly(audio, TARGET_RATE // gcd, self._native_rate // gcd).astype(np.float32)
