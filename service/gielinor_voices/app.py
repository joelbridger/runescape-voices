from __future__ import annotations

import argparse
import logging
import os
import signal
import sys
import threading
from pathlib import Path

from .controller import SpeechController
from .engine import ElevenLabsVoiceEngine, QwenVoiceEngine
from .server import VoiceHTTPServer


def _default_data_dir() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "GielinorVoices"
    return Path.home() / ".local" / "share" / "gielinor-voices"


def _default_token_file() -> Path:
    return Path.home() / ".runelite" / "gielinor-voices" / "token"


def _default_elevenlabs_key_file() -> Path:
    return _default_data_dir() / "secrets" / "elevenlabs-api-key"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Private local RuneScape voice service")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=17855)
    parser.add_argument("--token-file", type=Path, default=_default_token_file())
    parser.add_argument("--data-dir", type=Path, default=_default_data_dir())
    parser.add_argument(
        "--elevenlabs-key-file",
        type=Path,
        default=_default_elevenlabs_key_file(),
    )
    parser.add_argument("--log-file", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.host != "127.0.0.1":
        raise SystemExit("Gielinor Voices may listen only on 127.0.0.1")
    token = args.token_file.read_text(encoding="utf-8").strip()
    if not 32 <= len(token) <= 256:
        raise SystemExit("The private pairing token is missing or invalid")

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if args.log_file:
        args.log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(args.log_file, encoding="utf-8"))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )

    if args.elevenlabs_key_file.exists():
        engine_factory = lambda: ElevenLabsVoiceEngine(  # noqa: E731
            args.elevenlabs_key_file,
            args.data_dir / "elevenlabs-voices.json",
        )
        logging.getLogger(__name__).info(
            "Fast online voices are enabled; only visible dialogue is sent"
        )
    else:
        engine_factory = QwenVoiceEngine
        logging.getLogger(__name__).info(
            "No ElevenLabs key is installed; using the slower local voice engine"
        )
    controller = SpeechController(args.data_dir / "cache", engine_factory)
    controller.start()
    server = VoiceHTTPServer((args.host, args.port), token, controller)

    stopping = threading.Event()

    def stop_service(*_: object) -> None:
        if stopping.is_set():
            return
        stopping.set()
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGINT, stop_service)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, stop_service)

    logging.getLogger(__name__).info("Voice service listening privately on 127.0.0.1:%s", args.port)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
        controller.stop()


if __name__ == "__main__":
    main()
