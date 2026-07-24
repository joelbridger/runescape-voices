from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .models import SpeechRequest


@dataclass(frozen=True, slots=True)
class Performance:
    speaker: str
    instruction: str


VOICES = (
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

DELIVERIES = (
    "Speak clearly, naturally, and with grounded confidence.",
    "Speak thoughtfully, with a measured pace and quiet curiosity.",
    "Speak warmly, as if helping a familiar traveller.",
    "Speak with restrained theatrical energy suitable for a fantasy adventure.",
    "Speak cautiously, with alertness just beneath the surface.",
    "Speak with dry wit and a subtle sense of amusement.",
    "Speak formally, with calm authority and careful enunciation.",
    "Speak briskly and practically, like someone busy with important work.",
    "Speak gently, with patience and sincere concern.",
    "Speak boldly, with adventurous energy but without shouting.",
    "Speak mysteriously, with deliberate pauses and controlled intensity.",
    "Speak plainly and honestly, like an ordinary person in a lived-in world.",
)

# A small deliberate opening cast. Unknown characters still receive a permanent,
# deterministic pairing from the larger voice and delivery set.
NAMED_CAST: dict[str, Performance] = {
    "player": Performance(
        "Ryan",
        "Speak as a capable adventurer: alert, direct, and human rather than heroic or exaggerated.",
    ),
    "cook": Performance(
        "Uncle_Fu",
        "Speak as an experienced castle cook: warm, flustered, practical, and expressive.",
    ),
    "zanik": Performance(
        "Sohee",
        "Speak as a brave young cave goblin: curious, sincere, quick-thinking, and quietly determined.",
    ),
    "duke horacio": Performance(
        "Uncle_Fu",
        "Speak as a courteous noble ruler: calm, welcoming, and gently formal.",
    ),
    "hans": Performance(
        "Aiden",
        "Speak as a friendly castle groundskeeper: relaxed, observant, and unpretentious.",
    ),
    "king roald": Performance(
        "Uncle_Fu",
        "Speak with royal authority, impatience held in check, and clear formal diction.",
    ),
    "wise old man": Performance(
        "Uncle_Fu",
        "Speak as an eccentric, learned elder: assured, clever, and just a little mischievous.",
    ),
    "bob": Performance(
        "Eric",
        "Speak as a cheerful working tradesman: friendly, grounded, and energetic.",
    ),
    "oziach": Performance(
        "Uncle_Fu",
        "Speak as a gruff veteran: skeptical, seasoned, and difficult to impress.",
    ),
    "ariannwyn": Performance(
        "Dylan",
        "Speak as a disciplined elven leader: restrained, intelligent, and burdened by responsibility.",
    ),
    "elena": Performance(
        "Serena",
        "Speak as a compassionate and determined healer: intelligent, warm, and resolute.",
    ),
    "juna": Performance(
        "Serena",
        "Speak as an ancient guardian: serene, patient, mysterious, and untouched by haste.",
    ),
}


class CastingDirector:
    def performance_for(self, request: SpeechRequest) -> Performance:
        name_key = "player" if request.speaker_key == "player:local" else request.speaker_name.casefold()
        base = NAMED_CAST.get(name_key)
        if base is None:
            digest = hashlib.sha256(request.speaker_key.encode("utf-8")).digest()
            base = Performance(
                VOICES[digest[0] % len(VOICES)],
                DELIVERIES[digest[1] % len(DELIVERIES)],
            )
        emotion = self._emotion_for(request.text)
        instruction = base.instruction
        if emotion:
            instruction = f"{instruction} {emotion}"
        return Performance(base.speaker, instruction)

    @staticmethod
    def _emotion_for(text: str) -> str:
        lowered = text.casefold()
        if any(marker in lowered for marker in ("ha ha", "haha", "hehe", "hilarious")):
            return "Allow a genuine hint of laughter into this line."
        if any(marker in lowered for marker in ("help!", "run!", "look out", "hurry!")):
            return "Give this line urgent energy without becoming difficult to understand."
        if any(marker in lowered for marker in ("dead", "death", "killed", "murder")):
            return "Let the subject add appropriate gravity to the delivery."
        if text.rstrip().endswith("!"):
            return "Give this line a little more energy."
        if text.rstrip().endswith("?"):
            return "Make the question sound genuinely directed at the listener."
        return ""

