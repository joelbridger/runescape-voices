import pytest

from gielinor_voices.models import SpeechRequest


VALID = {
    "speakerKey": "npc:zanik",
    "speakerName": "Zanik",
    "text": "We will find a way.",
    "kind": "npc-dialogue",
    "sequence": 3,
    "volume": 0.85,
}


def test_accepts_only_the_reviewed_dialogue_shape() -> None:
    request = SpeechRequest.from_json(VALID)
    assert request.speaker_key == "npc:zanik"
    assert request.text == "We will find a way."
    assert request.is_dialogue


def test_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError):
        SpeechRequest.from_json({**VALID, "chat": "private"})


def test_rejects_unknown_dialogue_kinds() -> None:
    with pytest.raises(ValueError):
        SpeechRequest.from_json({**VALID, "kind": "private-chat"})


def test_rejects_oversized_text() -> None:
    with pytest.raises(ValueError):
        SpeechRequest.from_json({**VALID, "text": "x" * 1_201})

