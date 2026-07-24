# Gielinor Voices

Gielinor Voices gives visible Old School RuneScape dialogue private local AI
voice acting. It is designed for Jameson's legitimate RuneLite development
client and never controls the game.

## What it speaks

- NPC dialogue boxes
- The local player's dialogue boxes
- NPC overhead speech

It deliberately does **not** read public-player chat, private chat, friends,
inputs, movement, targets, inventory, bank data, credentials, or game memory.

## How it works

```text
Visible RuneLite dialogue
        |
        v
Thin read-only Java listener
        |
        | paired request to 127.0.0.1 only
        v
Private Windows voice service
        |
        +--> stable character casting
        +--> Qwen3-TTS local GPU speech
        +--> private repeated-line cache
        +--> Windows speakers
```

The local development launcher also loads the existing RuneScape Coach plugin,
so play-history recording and the paused coaching panel remain available in the
same client.

## Voice behavior

- Every speaker key receives a permanent, deterministic voice.
- Important characters can have deliberately written casting directions.
- The exact visible text is sent to the engine without rewriting.
- New dialogue replaces older queued dialogue.
- Closing or skipping dialogue stops playback.
- Repeated lines play from a private local cache.
- NPC overhead speech cannot interrupt an active dialogue box.

The first high-quality engine is
[Qwen3-TTS 0.6B CustomVoice](https://github.com/QwenLM/Qwen3-TTS). Its model and
generated recordings stay on the Windows PC. The casting layer is intentionally
separate so a later listening comparison can replace the speaking engine without
rewriting the RuneLite plugin.

## Development checks

Java listener and combined local client:

```bash
./gradlew clean test --no-daemon
```

Python service:

```bash
cd service
uv sync --extra dev
uv run pytest
```

The complete safety and maintenance explanation is in
[ARCHITECTURE.md](ARCHITECTURE.md).

## Start here when resuming

- [Pinned status](STATUS.md) — exactly what is installed, what was proved, and
  the one remaining human listening check.
- [Operations](OPERATIONS.md) — safe startup, checks, updates, and recovery.
- [Architecture](ARCHITECTURE.md) — how dialogue becomes local speech.
- [Agent rules](AGENTS.md) — boundaries that must never be weakened.
