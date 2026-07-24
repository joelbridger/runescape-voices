from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MAX_TEXT_LENGTH = 1_200
MAX_NAME_LENGTH = 120
ALLOWED_KINDS = {"npc-dialogue", "player-dialogue", "npc-overhead"}


@dataclass(frozen=True, slots=True)
class SpeechRequest:
    speaker_key: str
    speaker_name: str
    text: str
    kind: str
    sequence: int
    volume: float

    @classmethod
    def from_json(cls, value: Any) -> "SpeechRequest":
        if not isinstance(value, dict):
            raise ValueError("request must be an object")
        expected = {
            "speakerKey",
            "speakerName",
            "text",
            "kind",
            "sequence",
            "volume",
        }
        if set(value) != expected:
            raise ValueError("request fields do not match the approved shape")
        speaker_key = _clean_text(value["speakerKey"], "speakerKey", MAX_NAME_LENGTH)
        speaker_name = _clean_text(value["speakerName"], "speakerName", MAX_NAME_LENGTH)
        text = _clean_text(value["text"], "text", MAX_TEXT_LENGTH)
        kind = _clean_text(value["kind"], "kind", 40)
        if kind not in ALLOWED_KINDS:
            raise ValueError("unsupported dialogue kind")
        sequence = value["sequence"]
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ValueError("sequence must be a non-negative integer")
        volume = value["volume"]
        if isinstance(volume, bool) or not isinstance(volume, (int, float)):
            raise ValueError("volume must be a number")
        volume = float(volume)
        if not 0.0 <= volume <= 1.0:
            raise ValueError("volume must be between zero and one")
        return cls(speaker_key, speaker_name, text, kind, sequence, volume)

    @property
    def is_dialogue(self) -> bool:
        return self.kind.endswith("-dialogue")


def _clean_text(value: Any, field: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text")
    clean = value.strip()
    if not clean or len(clean) > maximum:
        raise ValueError(f"{field} has an invalid length")
    if any(ord(character) < 32 and not character.isspace() for character in clean):
        raise ValueError(f"{field} contains a control character")
    return clean

