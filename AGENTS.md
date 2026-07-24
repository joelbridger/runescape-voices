# Gielinor Voices rules

- This is a private, read-only RuneLite voice-acting system.
- It may observe only visible NPC dialogue widgets, the local player's dialogue
  widgets, NPC overhead text, and dialogue open/close events.
- Never read or transmit private chat, public-player chat, friends, credentials,
  inputs, position, targets, inventory, bank, or account-session data.
- Never click, type, select a dialogue choice, move the player, invoke a menu
  action, or otherwise control the game.
- The RuneLite plugin may connect only to the paired service on
  `127.0.0.1:17855`. It must not connect to the Internet.
- The service must bind only to `127.0.0.1` and require the private pairing
  token for speech and cancellation.
- Speak the exact visible words. Voice direction may change delivery but must
  never add, remove, summarize, or rewrite dialogue.
- Use original synthetic voices or properly licensed recordings. Never imitate
  a recognizable living actor, creator, or streamer without permission.
- Keep generated audio and model files local. Do not redistribute Jagex dialogue
  or a pre-generated quest-audio library.
- Keep blocking file, network, and model work off RuneLite's client thread.
- Run both Java and Python tests before saving a release.
- Only Jameson can confirm the final audible behavior inside the real game.

