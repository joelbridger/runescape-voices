# Gielinor Voices operations

This is the safe maintenance and recovery guide. Read
[STATUS.md](STATUS.md) first so a future session does not repeat completed work.

## Simple operating model

Two programs work together:

1. RuneLite notices approved visible dialogue and sends the exact words to the
   private address `127.0.0.1:17855`.
2. The local Windows service chooses a stable voice, creates or finds the audio,
   and plays it through the Windows speakers.

The service starts when Jameson signs in to Windows. The combined RuneLite
client opens only when Jameson uses the desktop shortcut or an authorized AI
starts its on-demand task.

## Safe read-only checks

From the Jameworld server, use the global `windows-desktop-ssh` skill and then:

```powershell
windows-pc run 'Get-ScheduledTask -TaskName "GielinorVoicesService","RuneScapeVoicesLocalLaunch" | Select-Object TaskName,State'
windows-pc run 'Invoke-RestMethod "http://127.0.0.1:17855/health" | ConvertTo-Json -Compress'
```

Healthy service output says `ready`, names either `elevenlabs:...` or `qwen3...`,
and has no error. It also reports the most recent first-sound delay in
`lastFirstAudioMs`. `loading` is normal while the local model is entering
graphics-card memory. Health never contains dialogue or a secret.

## Starting the programs

Start the background service:

```powershell
windows-pc run 'Start-ScheduledTask -TaskName "GielinorVoicesService"'
```

Open the combined development client:

```powershell
windows-pc run 'Start-ScheduledTask -TaskName "RuneScapeVoicesLocalLaunch"'
```

Do not open the older `RuneScapeCoachLocalLaunch` task at the same time. The
voice launcher already includes RuneScape Coach.

## Logs and private data

The safe service log is:

```text
%LOCALAPPDATA%\GielinorVoices\runtime\service.log
```

It records startup and model errors but does not intentionally log dialogue or
the pairing key. Read only the smallest useful tail when diagnosing a failure.

Generated WAV files live in the private runtime cache. They may contain game
dialogue, so do not upload or commit them. Models, environments, caches, logs,
pairing keys, and RuneLite credentials never belong in Git.

Never read or display:

- `%USERPROFILE%\.runelite\gielinor-voices\token`
- `%USERPROFILE%\.runelite\credentials.properties`
- `%LOCALAPPDATA%\GielinorVoices\runtime\secrets\elevenlabs-api-key`

Checking that these files exist is allowed when needed.

## Fast online voice mode

The online path is optional. The service selects it automatically when the
protected ElevenLabs key file exists. Its setup helper asks Jameson to paste the
key into a hidden prompt, locks the folder to his Windows user, and restarts the
service. Do not pass the key on a command line because command history can save
it.

The helper is served privately as `/voice-online-setup.ps1`. Confirm health
names `elevenlabs:eleven_flash_v2_5` after setup. Only visible dialogue is sent
to ElevenLabs. Deleting the key file and restarting the task returns the service
to fully local Qwen speech.

## Tests

On the Ubuntu server:

```bash
cd /home/jameson/runescape-voices
./gradlew clean test --no-daemon
cd service
uv sync --frozen --extra dev --python 3.12
uv run pytest
```

The private Windows installer repeats both test groups on the PC before it
creates or replaces the Windows tasks.

## Updating the installed build

The source of truth is split between two repositories:

- `/home/jameson/runescape-voices` contains the listener and voice service.
- `/home/jameson/RuneScape` contains the private verified Windows installer.

For a real code update:

1. Make the smallest safe change in `runescape-voices`.
2. Run the Java and Python tests once.
3. Save and push the voice repository.
4. Download that exact GitHub source archive and calculate its SHA-256.
5. Update the exact voice commit and archive hash in
   `/home/jameson/RuneScape/integrations/runelite/windows/Install-GielinorVoices.ps1`.
6. Update the matching installer test in the RuneScape Coach repository.
7. Run `bun test`, `bun run typecheck`, and `git diff --check` there.
8. Save and push the RuneScape Coach repository.
9. Restart the private receiver so `/voice-installer.ps1` serves the new pinned
   installer.
10. Run the installer on Windows through `windows-pc`, verify health, and open
    the combined client.

Never replace the verified archive with an unpinned branch download.

## Recovery order

If voice acting stops:

1. Check service health.
2. If health says `loading`, leave the model alone and check again.
3. If health says `error`, read the small tail of `service.log`.
4. If online speech fails, check the ElevenLabs plan/key without printing the
   key. Removing the key file safely returns to local speech.
5. Restart only `GielinorVoicesService`.
6. If the plugin is absent, close the combined local client and start
   `RuneScapeVoicesLocalLaunch` again.
7. Reinstall only when source, tasks, or the isolated Python environment is
   actually missing or broken.

Do not delete the model cache as a first repair. Do not weaken the loopback
address or pairing check. Do not modify the normal RuneLite installation.
