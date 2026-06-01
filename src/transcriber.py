import os
import re
from pathlib import Path
from typing import Optional, Type
import numpy as np

MODEL_NAME = "small"
_MODEL_DIR = str(Path(os.environ.get("APPDATA", Path.home())) / "MurmurAI" / "models")

# Common Whisper hallucinations on short/silent/unclear audio — suppress these
_HALLUCINATIONS = {
    "thank you.", "thank you", "thanks.", "thanks",
    "thank you very much.", "thank you very much", "thank you very",
    "thank you for watching.", "thank you for watching",
    "thanks for watching.", "thanks for watching",
    "you", "you.", "bye.", "bye", "goodbye.", "goodbye",
    "please subscribe.", "please subscribe",
    ".", "..", "...", "♪", "♪♪", "[music]", "[applause]",
}


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
            beam_size=2,                  # balance: faster than 5, better than 1
            vad_filter=True,              # strips trailing silence → prevents hallucinations
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )
        # Collapse whitespace from segment gaps, then strip
        text = re.sub(r"\s+", " ", "".join(s.text for s in segments)).strip()
        return "" if _is_hallucination(text) else text

    def set_language(self, language: str) -> None:
        self._language = None if language == "auto" else language


def _is_hallucination(text: str) -> bool:
    return text.lower().strip() in _HALLUCINATIONS or len(text.strip()) <= 1
