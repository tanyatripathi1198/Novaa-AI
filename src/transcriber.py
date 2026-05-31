import os
from pathlib import Path
from typing import Optional, Type
import numpy as np

MODEL_NAME = "small"
_MODEL_DIR = str(Path(os.environ.get("APPDATA", Path.home())) / "MurmurAI" / "models")


class Transcriber:
    def __init__(
        self,
        language: str = "auto",
        _model_cls: Optional[Type] = None,
    ) -> None:
        self._language: Optional[str] = None if language == "auto" else language
        self._model = None
        self._model_cls = _model_cls   # injected in tests

    def load(self) -> None:
        if self._model is not None:
            return
        if self._model_cls is None:
            try:
                from faster_whisper import WhisperModel as cls
            except ImportError as exc:
                raise RuntimeError(
                    "faster_whisper is not installed. Run: pip install faster-whisper"
                ) from exc
        else:
            cls = self._model_cls
        self._model = cls(
            MODEL_NAME,
            device="cpu",
            compute_type="int8",
            download_root=_MODEL_DIR,
        )

    def transcribe(self, audio: np.ndarray) -> str:
        if self._model is None:
            raise RuntimeError("Call load() before transcribe()")
        segments, _ = self._model.transcribe(
            audio,
            language=self._language,
            beam_size=1,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        return "".join(s.text for s in segments).strip()

    def set_language(self, language: str) -> None:
        self._language = None if language == "auto" else language
