from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

from gielinor_voices.casting import Performance
from gielinor_voices.engine import ElevenLabsVoiceEngine


class FakeResponse:
    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = iter(chunks)

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, _: int = -1) -> bytes:
        return next(self._chunks, b"")


def _files(tmp_path: Path) -> tuple[Path, Path]:
    key_file = tmp_path / "key"
    key_file.write_text("sk_" + "x" * 48, encoding="utf-8")
    catalog_file = tmp_path / "voices.json"
    catalog_file.write_text(
        json.dumps({"voiceIds": ["voice-one", "voice-two"]}),
        encoding="utf-8",
    )
    return key_file, catalog_file


def test_elevenlabs_streams_raw_pcm_without_exposing_the_key(tmp_path: Path) -> None:
    key_file, catalog_file = _files(tmp_path)
    calls: list[Any] = []

    def opener(request: Any, **_: object) -> FakeResponse:
        calls.append(request)
        samples = np.array([-32768, 0, 16384, 32767], dtype="<i2")
        raw = samples.tobytes()
        return FakeResponse([raw[:3], raw[3:]])

    engine = ElevenLabsVoiceEngine(
        key_file,
        catalog_file,
        api_root="https://voices.invalid",
        opener=opener,
    )
    chunks = list(
        engine.stream(
            "Hello, adventurer.",
            Performance("Vivian", "Speak warmly."),
        )
    )

    waveform = np.concatenate(chunks)
    assert np.allclose(waveform, [-1.0, 0.0, 0.5, 32767 / 32768])
    assert len(calls) == 1
    request = calls[0]
    assert request.full_url.endswith(
        "/v1/text-to-speech/voice-one/stream?output_format=pcm_24000"
    )
    assert request.headers["Xi-api-key"] == "sk_" + "x" * 48
    payload = json.loads(request.data)
    assert payload["text"] == "Hello, adventurer."
    assert payload["model_id"] == "eleven_flash_v2_5"
    assert "Speak warmly" not in request.data.decode("utf-8")


def test_elevenlabs_error_message_never_contains_key_or_dialogue(tmp_path: Path) -> None:
    key_file, catalog_file = _files(tmp_path)

    def opener(*_: object, **__: object) -> FakeResponse:
        raise OSError("network failed")

    engine = ElevenLabsVoiceEngine(key_file, catalog_file, opener=opener)
    try:
        list(
            engine.stream(
                "A very private test sentence.",
                Performance("Serena", "Speak quietly."),
            )
        )
        raise AssertionError("stream unexpectedly succeeded")
    except RuntimeError as error:
        message = str(error)
        assert "sk_" not in message
        assert "private test" not in message


def test_elevenlabs_fetches_and_saves_available_voice_catalog(tmp_path: Path) -> None:
    key_file = tmp_path / "key"
    key_file.write_text("sk_" + "x" * 48, encoding="utf-8")
    catalog_file = tmp_path / "voices.json"
    payload = json.dumps(
        {
            "voices": [
                {
                    "voice_id": "male-voice",
                    "name": "Bram",
                    "labels": {"gender": "male"},
                },
                {
                    "voice_id": "female-voice",
                    "name": "Ada",
                    "labels": {"gender": "female"},
                },
            ]
        }
    ).encode("utf-8")

    def opener(*_: object, **__: object) -> FakeResponse:
        return FakeResponse([payload])

    engine = ElevenLabsVoiceEngine(key_file, catalog_file, opener=opener)

    assert engine.identity.startswith("elevenlabs:eleven_flash_v2_5:")
    assert json.loads(catalog_file.read_text(encoding="utf-8")) == {
        "voiceIds": ["female-voice", "male-voice"]
    }
