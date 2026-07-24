from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

import numpy as np

from .casting import Performance


LOGGER = logging.getLogger(__name__)
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"


class VoiceEngine(Protocol):
    @property
    def identity(self) -> str: ...

    def generate(self, text: str, performance: Performance) -> tuple[np.ndarray, int]: ...


class QwenVoiceEngine:
    def __init__(self, model_path: str | Path = MODEL_ID) -> None:
        import torch
        from qwen_tts import Qwen3TTSModel

        if not torch.cuda.is_available():
            raise RuntimeError("The NVIDIA voice engine is unavailable")
        LOGGER.info("Loading the local Qwen voice model")
        self._model = Qwen3TTSModel.from_pretrained(
            str(model_path),
            device_map="cuda:0",
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
        )
        self._identity = f"qwen3-tts-0.6b-custom-v1:{Path(str(model_path)).name}"
        LOGGER.info("The local Qwen voice model is ready")

    @property
    def identity(self) -> str:
        return self._identity

    def generate(self, text: str, performance: Performance) -> tuple[np.ndarray, int]:
        waveforms, sample_rate = self._model.generate_custom_voice(
            text=text,
            language="English",
            speaker=performance.speaker,
            instruct=performance.instruction,
        )
        waveform = np.asarray(waveforms[0], dtype=np.float32).reshape(-1)
        if waveform.size == 0 or not np.isfinite(waveform).all():
            raise RuntimeError("The voice engine returned invalid audio")
        return waveform, int(sample_rate)

