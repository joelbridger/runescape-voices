# Gielinor Voices architecture

## Components

| Part | Responsibility |
|---|---|
| `GielinorVoicesPlugin` | Observes approved visible dialogue events and creates exact speech requests. |
| `VoiceServiceClient` | Sends authenticated JSON only to the fixed loopback address. |
| `SpeechController` | Keeps the newest useful line, cancels skipped lines, manages playback, and caches audio. |
| `CastingDirector` | Gives each character a stable voice and performance direction. |
| `QwenVoiceEngine` | Generates local high-quality speech on the NVIDIA GPU. |
| `VoiceHTTPServer` | Exposes health, speech, and cancellation only on `127.0.0.1`. |
| `vendor/runescape-coach-plugin` | Pinned public coaching plugin loaded beside voices in the local development client. |

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

Model generation cannot always be interrupted safely inside a GPU call. When a
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
Qwen3-TTS receives the exact text plus a separate delivery instruction.

## Combined legitimate local client

The repository includes the existing public RuneScape Coach plugin as a pinned
Git submodule. The test launcher loads both plugins with RuneLite's official
external-plugin development mechanism. It does not patch or inject into the
normal RuneLite client.

The ordinary Plugin Hub RuneScape Coach submission remains separate and
unchanged.

