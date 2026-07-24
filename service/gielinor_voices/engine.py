from __future__ import annotations

import logging
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterator
from typing import Any, Callable, Protocol, runtime_checkable
import urllib.request

import numpy as np

from .casting import Performance


LOGGER = logging.getLogger(__name__)
MODEL_ID = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"
ELEVENLABS_MODEL_ID = "eleven_flash_v2_5"
ELEVENLABS_SAMPLE_RATE = 24_000
ELEVENLABS_API_ROOT = "https://api.elevenlabs.io"


@dataclass(frozen=True, slots=True)
class OnlineVoice:
    voice_id: str
    gender: str


@runtime_checkable
class VoiceEngine(Protocol):
    @property
    def identity(self) -> str: ...


@runtime_checkable
class CompleteVoiceEngine(VoiceEngine, Protocol):
    def generate(self, text: str, performance: Performance) -> tuple[np.ndarray, int]: ...


@runtime_checkable
class StreamingVoiceEngine(VoiceEngine, Protocol):
    @property
    def sample_rate(self) -> int: ...

    def stream(self, text: str, performance: Performance) -> Iterator[np.ndarray]: ...


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


class ElevenLabsVoiceEngine:
    """Low-latency, streamed speech using ElevenLabs Flash.

    The API key remains in a local file owned by the Windows user. Only the
    visible line of dialogue and the chosen voice ID leave the computer.
    """

    _SPEAKER_SLOTS = (
        "Vivian",
        "Serena",
        "Uncle_Fu",
        "Dylan",
        "Eric",
        "Ryan",
        "Aiden",
        "Ono_Anna",
        "Sohee",
    )
    _FEMALE_SPEAKERS = frozenset({"Vivian", "Serena", "Ono_Anna", "Sohee"})
    _MALE_SPEAKERS = frozenset({"Uncle_Fu", "Dylan", "Eric", "Ryan", "Aiden"})

    def __init__(
        self,
        api_key_file: Path,
        catalog_file: Path,
        *,
        api_root: str = ELEVENLABS_API_ROOT,
        opener: Callable[..., Any] = urllib.request.urlopen,
    ) -> None:
        api_key = api_key_file.read_text(encoding="utf-8").strip()
        if not 20 <= len(api_key) <= 256 or any(character.isspace() for character in api_key):
            raise RuntimeError("The ElevenLabs API key is missing or invalid")
        self._api_key = api_key
        self._api_root = api_root.rstrip("/")
        self._opener = opener
        self._voices = self._load_or_fetch_voices(catalog_file)
        catalog_digest = hashlib.sha256(
            "\n".join(
                f"{voice.gender}:{voice.voice_id}" for voice in self._voices
            ).encode("utf-8")
        ).hexdigest()[:12]
        self._identity = f"elevenlabs:{ELEVENLABS_MODEL_ID}:pcm24k:{catalog_digest}"
        LOGGER.info(
            "ElevenLabs streaming voice engine is ready with %s character voices",
            len(self._voices),
        )

    @property
    def identity(self) -> str:
        return self._identity

    @property
    def sample_rate(self) -> int:
        return ELEVENLABS_SAMPLE_RATE

    def stream(self, text: str, performance: Performance) -> Iterator[np.ndarray]:
        voice_id = self._voice_for(performance)
        url = (
            f"{self._api_root}/v1/text-to-speech/{voice_id}/stream"
            f"?output_format=pcm_{ELEVENLABS_SAMPLE_RATE}"
        )
        body = json.dumps(
            {
                "text": text,
                "model_id": ELEVENLABS_MODEL_ID,
                "language_code": "en",
                "voice_settings": {
                    "stability": 0.42,
                    "similarity_boost": 0.72,
                    "style": 0.0,
                    "use_speaker_boost": False,
                    "speed": 1.0,
                },
            },
            ensure_ascii=False,
        ).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/octet-stream",
                "xi-api-key": self._api_key,
                "User-Agent": "GielinorVoices/0.2",
            },
            method="POST",
        )
        remainder = b""
        try:
            with self._opener(request, timeout=15) as response:
                while chunk := response.read(8192):
                    pcm = remainder + chunk
                    usable = len(pcm) - (len(pcm) % 2)
                    if usable:
                        waveform = np.frombuffer(pcm[:usable], dtype="<i2").astype(
                            np.float32
                        )
                        waveform /= 32768.0
                        yield waveform
                    remainder = pcm[usable:]
        except Exception as exception:
            raise RuntimeError(
                f"ElevenLabs could not create this line ({type(exception).__name__})"
            ) from exception
        if remainder:
            raise RuntimeError("ElevenLabs returned incomplete audio")

    def _voice_for(self, performance: Performance) -> str:
        desired_gender = self._gender_for(performance.speaker)
        candidates = tuple(
            voice for voice in self._voices if voice.gender == desired_gender
        )
        if not candidates:
            candidates = self._voices
        try:
            slot = self._SPEAKER_SLOTS.index(performance.speaker)
        except ValueError:
            digest = hashlib.sha256(performance.speaker.encode("utf-8")).digest()
            slot = int.from_bytes(digest[:4], "big")
        return candidates[slot % len(candidates)].voice_id

    def _gender_for(self, speaker: str) -> str:
        if speaker in self._MALE_SPEAKERS:
            return "male"
        if speaker in self._FEMALE_SPEAKERS:
            return "female"
        return "other"

    def _load_or_fetch_voices(self, catalog_file: Path) -> tuple[OnlineVoice, ...]:
        if catalog_file.exists():
            try:
                catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
                voices = self._validate_catalog(catalog)
                if voices:
                    return voices
            except (OSError, ValueError, json.JSONDecodeError):
                LOGGER.warning("The saved ElevenLabs voice list was invalid; refreshing it")

        request = urllib.request.Request(
            f"{self._api_root}/v2/voices?page_size=100&include_total_count=false",
            headers={
                "Accept": "application/json",
                "xi-api-key": self._api_key,
                "User-Agent": "GielinorVoices/0.2",
            },
        )
        try:
            with self._opener(request, timeout=15) as response:
                payload = json.load(response)
        except Exception as exception:
            raise RuntimeError(
                f"ElevenLabs voices could not be loaded ({type(exception).__name__})"
            ) from exception

        voices = payload.get("voices") if isinstance(payload, dict) else None
        if not isinstance(voices, list):
            raise RuntimeError("ElevenLabs returned an invalid voice list")
        candidates: list[tuple[str, str, str]] = []
        for voice in voices:
            if not isinstance(voice, dict):
                continue
            voice_id = voice.get("voice_id")
            name = voice.get("name")
            labels = voice.get("labels")
            gender = labels.get("gender", "") if isinstance(labels, dict) else ""
            if (
                isinstance(voice_id, str)
                and 8 <= len(voice_id) <= 80
                and isinstance(name, str)
            ):
                candidates.append((gender.casefold(), name.casefold(), voice_id))
        candidates.sort(key=lambda item: (item[1], item[2]))
        groups: dict[str, list[str]] = {"female": [], "male": [], "other": []}
        for gender, _, voice_id in candidates:
            group = gender if gender in {"female", "male"} else "other"
            groups[group].append(voice_id)
        selected: list[OnlineVoice] = []
        while len(selected) < 18 and any(groups.values()):
            for group in ("female", "male", "other"):
                if groups[group]:
                    selected.append(OnlineVoice(groups[group].pop(0), group))
                    if len(selected) == 18:
                        break
        if not selected:
            raise RuntimeError("No ElevenLabs voices are available for this account")

        catalog_file.parent.mkdir(parents=True, exist_ok=True)
        temporary = catalog_file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "voices": [
                        {"voiceId": voice.voice_id, "gender": voice.gender}
                        for voice in selected
                    ]
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(catalog_file)
        return tuple(selected)

    @staticmethod
    def _validate_catalog(value: Any) -> tuple[OnlineVoice, ...]:
        if not isinstance(value, dict) or set(value) != {"voices"}:
            return ()
        values = value["voices"]
        if not isinstance(values, list):
            return ()
        clean: list[OnlineVoice] = []
        for item in values:
            if not isinstance(item, dict) or set(item) != {"voiceId", "gender"}:
                return ()
            voice_id = item["voiceId"]
            gender = item["gender"]
            if (
                not isinstance(voice_id, str)
                or not 8 <= len(voice_id) <= 80
                or gender not in {"female", "male", "other"}
            ):
                return ()
            clean.append(OnlineVoice(voice_id, gender))
        return tuple(clean)
