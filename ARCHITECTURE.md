# Gielinor Voices architecture

## Components

| Part | Responsibility |
|---|---|
| `GielinorVoicesPlugin` | Observes approved visible dialogue events and creates exact speech requests. |
| `VoiceServiceClient` | Sends authenticated JSON only to the fixed loopback address. |
| `SpeechController` | Keeps the newest useful line, cancels skipped lines, manages playback, and caches audio. |
| `CastingDirector` | Gives each character a stable voice and performance direction. |
| `ElevenLabsVoiceEngine` | Streams low-delay PCM speech from ElevenLabs Flash when Jameson enables it. |
| `QwenVoiceEngine` | Generates local high-quality speech on the NVIDIA GPU. |
| `VoiceHTTPServer` | Exposes health, speech, and cancellation only on `127.0.0.1`. |
| `vendor/runescape-coach-plugin` | Pinned public coaching plugin loaded beside voices in the local development client. |

## Complete data flow

1. RuneLite raises a normal widget or overhead-text event.
2. `GielinorVoicesPlugin` accepts only the configured NPC dialogue, local-player
   dialogue, or NPC overhead surface.
3. RuneLite formatting tags are removed, but the words are not rewritten.
4. `SpeakerKeys` makes a stable identity from the player, NPC name, NPC ID, or
   visible head model.
5. `VoiceServiceClient` sends the approved JSON shape to the fixed loopback
   address with the private pairing header. This work stays off RuneLite's game
   thread.
6. `VoiceHTTPServer` checks the address, pairing key, body size, exact fields,
   field types, and allowed dialogue kind.
7. `SpeechController` applies priority and cancellation rules.
8. `CastingDirector` maps the stable speaker to a permanent voice slot. Important
   named characters use written cast choices; other characters use a repeatable
   hash.
9. The cache looks for an exact prior recording.
10. When an ElevenLabs key is installed, the service streams 24 kHz raw speech
    from Flash v2.5 and begins playback with the first chunk. It records the
    first-sound delay in health status as `lastFirstAudioMs`.
11. Without that key, `QwenVoiceEngine` creates the complete waveform on the
    local NVIDIA GPU before playback.
12. The finished WAV is stored privately. Skipped speech is stopped and an
    incomplete streamed line is never cached.

The server, dashboard, Wiki library, and Character Export pipeline do not sit in
this speech path. Voice acting still works if the home server is unavailable.

## Approved request

The Java plugin sends only:

```json
{
  "speakerKey": "npc:zanik",
  "speakerName": "Zanik",
  "text": "Exact visible dialogue",
  "kind": "npc-dialogue",
  "sequence": 42,
  "volume": 0.85
}
```

The service rejects missing, extra, oversized, malformed, or unsupported fields.
The pairing token is carried in the request header and never logged.

## Queue rules

Dialogue-box lines have priority over overhead speech. A new dialogue line
replaces the old pending line and stops old playback. NPC overhead speech is
ignored while a dialogue-box line is being generated, queued, or played.

Local model generation cannot always be interrupted safely inside a GPU call. When a
line is skipped during generation, its result is discarded and never played.
The newest line proceeds next. Cached lines can stop and change immediately.

## Cache

The cache key covers:

- engine identity;
- permanent character identity;
- selected model speaker;
- delivery instructions; and
- exact visible text.

Changing any of these creates a new recording. Files are private WAV recordings
under the installed service data directory. The cache removes the oldest used
files after reaching its size limit.

## Safety boundary

The plugin contains no game-input, menu-action, movement, camera, inventory,
bank, credential, packet, reflection, or process-memory code. It does not read
player chat. Its only network destination is the compile-time loopback address.

The service refuses to bind to a LAN or Internet address. Speech and cancellation
require a random token shared through the user's private RuneLite data folder.
Health exposes only engine readiness, not dialogue or credentials.

The service does not rewrite text or call a language model for story content.
Qwen3-TTS receives the exact text plus a separate delivery instruction. The
online engine receives only the exact visible text, one selected voice ID, and
ordinary voice controls. The ElevenLabs key stays in an access-protected file
under the Windows service data folder and never enters RuneLite, logs, health,
Git, or the Jameworld server.

## Combined legitimate local client

The repository includes the existing public RuneScape Coach plugin as a pinned
Git submodule. The test launcher loads both plugins with RuneLite's official
external-plugin development mechanism. It does not patch or inject into the
normal RuneLite client.

The ordinary Plugin Hub RuneScape Coach submission remains separate and
unchanged.

The Windows installer, task names, local paths, checks, and recovery steps are
recorded in [OPERATIONS.md](OPERATIONS.md). The exact live pause point is
[STATUS.md](STATUS.md).
