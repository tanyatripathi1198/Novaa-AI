import os
import re
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
        self._model_cls = _model_cls

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
            beam_size=5,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )
        # Use faster-whisper's per-segment confidence instead of content blacklists.
        # no_speech_prob > 0.6 means the model itself thinks this is not speech — skip it.
        # This allows "thank you", names, unusual phrases to pass through unfiltered.
        parts = [
            s.text for s in segments
            if s.no_speech_prob < 0.6
        ]
        text = re.sub(r"\s+", " ", "".join(parts)).strip()
        return text

    def set_language(self, language: str) -> None:
        self._language = None if language == "auto" else language
