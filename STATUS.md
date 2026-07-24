# Gielinor Voices — pinned status

## Pause point

Jameson heard a real NPC line through the combined RuneLite client. The complete
local system works, but the unseen line took roughly 30 seconds to begin. The
current work replaces that slow live miss with streamed ElevenLabs Flash speech.
The hard acceptance target is `lastFirstAudioMs` at or below 1,000 on a real
uncached NPC line.

The streamed engine is now installed and active. A fresh uncached loopback test
reached first audio in **844 ms**, with no service error. This passes the
one-second technical target. Jameson then confirmed that it worked during real
game dialogue.

Orc_Bane55's own dialogue is deliberately cast as the male adventurer voice
`Ryan`. The online picker now also guarantees that this cast uses an
ElevenLabs voice labeled male.

## Latest runtime finding

Jameson later closed several PowerShell windows and then found that RuneLite
dialogue was silent. A read-only Windows check proved:

- `GielinorVoicesService` was installed but stopped;
- `RuneScapeVoicesLocalLaunch` was installed but stopped;
- ordinary `RuneLite.exe` was open on Orc Bane; and
- `http://127.0.0.1:17855/health` was unreachable.

This means the installed files are still safe, but neither half of the voice
system is present in the current play session. Ordinary RuneLite cannot load
this private development plugin.

The active ordinary client was deliberately left open because Jameson was using
it. To resume, first preserve the safe in-game position and close ordinary
RuneLite, then start `GielinorVoicesService` and
`RuneScapeVoicesLocalLaunch`. Verify health says `ready` before testing NPC
dialogue. Do not reinstall unless those existing tasks or installed files are
actually broken.

Jameson then explicitly requested the switch. Ordinary RuneLite closed cleanly,
the existing service task started, health returned `ready`, and the combined
voice-and-coach RuneLite window opened successfully. The installed build is
therefore running again. Jameson then heard a real NPC line, proving the full
path. Its roughly 30-second delay was not acceptable.

Direct tests on the real PC found the cause:

- local Qwen waits for the whole waveform before playback;
- its installed Python interface does not expose true audio streaming;
- local Kokoro loaded in 1.400 seconds, then needed 2.761 seconds for a tiny
  line, 5.162 seconds for a medium line, and 8.443 seconds for a longer line;
- therefore neither tested local path can meet the one-second requirement.

The chosen design uses ElevenLabs Flash v2.5 for a new uncached line, streams
raw audio directly to the speakers, keeps stable character casting, and saves
the finished line in the private cache. Qwen remains the no-key local choice.

## What is installed

- Windows desktop shortcut: `RuneScape Voices (Local)`
- Background task: `GielinorVoicesService`
- Combined RuneLite task: `RuneScapeVoicesLocalLaunch`
- Voice listener source:
  `%LOCALAPPDATA%\GielinorVoices\source-e318c014d2af77d3286b63d3a3e0e8895542f460`
- Service environment:
  `%LOCALAPPDATA%\GielinorVoices\service`
- Models, cache, and service log:
  `%LOCALAPPDATA%\GielinorVoices\runtime`
- Private pairing key:
  `%USERPROFILE%\.runelite\gielinor-voices\token`

Never read, print, copy, or upload the pairing key. Never read RuneLite's
`credentials.properties`. The installed programs use those files privately.

The installed voice source is commit
`e318c014d2af77d3286b63d3a3e0e8895542f460`. It includes the RuneScape Coach
plugin pinned at `736ab5f8`. The private installer verifies both downloaded
archives before using them.

The updated service is running and health names the ElevenLabs Flash engine.
It loaded the refreshed gender-aware voice list with no startup error.

## What has been proved

- Fourteen Python voice-service tests passed on the actual Windows installation.
- The voice and coach Java tests passed together in a clean Windows build.
- The service reports `ready` with no error.
- Qwen3-TTS 0.6B CustomVoice loaded on the RTX 5070.
- A real line generated, played, and produced a private cached WAV file.
- A second unseen line generated successfully after warm-up.
- A request without the private pairing key was rejected.
- The combined RuneLite window opened with both plugin classes loaded through
  RuneLite's official development-client path.
- Jameson confirmed that fast speech worked in the real game.
- Player casting tests prove that `player:local` selects the deliberate male
  cast and a provider voice labeled male.
- The server and voice repositories are clean, saved, and backed up on GitHub.

## Current provider allowance

After the successful live test, ElevenLabs began returning HTTP 402, meaning the
account had no API speech allowance available for new lines. This explained why
Jameson heard cached NPC speech but not a new player line. Jameson then upgraded
the account to the Starter plan himself. The ElevenLabs account page confirms
Starter is active, and the Windows voice service is running `ready` with no
error. Jameson then confirmed that the male player voice works great in the
real game. The online voice system is fully accepted.

## RuneScape coaching checkpoint

Voice work did not move the account. The separate RuneScape Coach project is
paused outside the Recipe for Disaster banquet room after the opening banquet
scene. No frozen guest has been inspected yet. The next recommended subquest is
the Goblin Generals. The authoritative instructions are in:

- `/home/jameson/RuneScape/plans/CURRENT.md`
- `/home/jameson/RuneScape/plans/FORWARD.md`

Dashboard and coaching-plan publication remain paused.

## Problems already solved

1. The Windows PowerShell runtime lacked
   `RandomNumberGenerator.Fill`. The installer uses the compatible
   cryptographic API instead.
2. Qwen's loose dependency request selected old audio packages that did not
   support Python 3.12. The service now pins the tested modern package set.
3. The normal RuneLite window did not finish a gentle close. Only that old
   process was closed, and the combined client then opened normally.
4. The old Python speaker survived one scheduled-task replacement and held port
   17855. Only the two proven old voice processes were stopped. Both setup
   helpers now verify the exact installed voice command before stopping it and
   refuse to stop an unrelated program.
5. The online setup stored the key under `runtime/secrets`, while the first
   service build looked one folder higher. The service now derives the protected
   key path from its selected data folder, with a regression test.
6. The first dedicated provider key appeared in a diagnostic capture. It was
   deleted before use. Its restricted replacement was transferred without
   printing it, and the temporary server copy was securely removed.
7. The first online catalog kept voice IDs but discarded gender labels, so a
   male local cast did not prove a male provider voice. The installed build now
   preserves those labels and limits Orc_Bane55's cast to male-labeled voices.
8. Silence after the successful live test was not a RuneLite player-dialogue
   failure. The service log proved that the request reached ElevenLabs and was
   rejected with HTTP 402 because the speech allowance was empty.

These fixes are already in source and must not be undone.
