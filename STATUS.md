# Gielinor Voices — pinned status

## Pause point

The private voice system is built and installed on Jameson's Windows PC. Its
current running state is recorded below. Work is deliberately paused before the
first real in-game listening check.

Do not rebuild or reinstall it merely because a new session begins. Resume with
the listening check below.

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

## What is installed

- Windows desktop shortcut: `RuneScape Voices (Local)`
- Background task: `GielinorVoicesService`
- Combined RuneLite task: `RuneScapeVoicesLocalLaunch`
- Voice listener source:
  `%LOCALAPPDATA%\GielinorVoices\source-62f95ed083f5ea13562defb97525236d3bfb28a3`
- Service environment:
  `%LOCALAPPDATA%\GielinorVoices\service`
- Models, cache, and service log:
  `%LOCALAPPDATA%\GielinorVoices\runtime`
- Private pairing key:
  `%USERPROFILE%\.runelite\gielinor-voices\token`

Never read, print, copy, or upload the pairing key. Never read RuneLite's
`credentials.properties`. The installed programs use those files privately.

The installed voice source is commit
`62f95ed083f5ea13562defb97525236d3bfb28a3`. It includes the RuneScape Coach
plugin pinned at `736ab5f8`. The private installer verifies both downloaded
archives before using them.

## What has been proved

- Eight Python voice-service tests passed on the actual Windows installation.
- The voice and coach Java tests passed together in a clean Windows build.
- The service reports `ready` with no error.
- Qwen3-TTS 0.6B CustomVoice loaded on the RTX 5070.
- A real line generated, played, and produced a private cached WAV file.
- A second unseen line generated successfully after warm-up.
- A request without the private pairing key was rejected.
- The combined RuneLite window opened with both plugin classes loaded through
  RuneLite's official development-client path.
- The server and voice repositories are clean, saved, and backed up on GitHub.

## What has not been proved yet

Only Jameson can prove the final experience through the real speakers:

1. Open the already-running combined RuneLite window, or use
   `RuneScape Voices (Local)` on the desktop.
2. Log in manually if needed.
3. Talk to any NPC. The Lumbridge Cook is a useful choice because that is also
   the saved coaching destination.
4. Leave the first line visible until it speaks.
5. Advance or close the dialogue and confirm the old line stops.
6. Report whether the voice was heard, whether it fit the character, and whether
   the pause before speech felt acceptable.

No game input may be automated for this test.

## RuneScape coaching checkpoint

Voice work did not move the account. The separate RuneScape Coach project
remains paused after **Death to the Dorgeshuun** and before finishing
**Cook's Assistant**. Character Export snapshot 007433 remains the proven
carried state. The authoritative instructions are in:

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

These fixes are already in source and must not be undone.
