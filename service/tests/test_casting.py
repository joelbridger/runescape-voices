from gielinor_voices.casting import CastingDirector
from gielinor_voices.models import SpeechRequest


def request(key: str, name: str = "Unknown") -> SpeechRequest:
    return SpeechRequest(key, name, "Where are you going?", "npc-dialogue", 1, 1.0)


def test_named_character_has_a_deliberate_cast() -> None:
    performance = CastingDirector().performance_for(request("npc:zanik", "Zanik"))
    assert performance.speaker == "Sohee"
    assert "cave goblin" in performance.instruction


def test_local_player_has_a_deliberate_male_cast() -> None:
    performance = CastingDirector().performance_for(
        SpeechRequest(
            "player:local",
            "Player",
            "I will take care of it.",
            "player-dialogue",
            1,
            1.0,
        )
    )
    assert performance.speaker == "Ryan"
    assert "capable adventurer" in performance.instruction


def test_unknown_character_cast_is_stable() -> None:
    director = CastingDirector()
    first = director.performance_for(request("npc:guard"))
    second = director.performance_for(request("npc:guard"))
    assert first == second


def test_different_characters_receive_variety() -> None:
    director = CastingDirector()
    performances = {
        director.performance_for(request(f"npc:character-{index}"))
        for index in range(30)
    }
    assert len(performances) >= 10
