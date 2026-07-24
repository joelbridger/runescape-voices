from __future__ import annotations

from pathlib import Path

from gielinor_voices.app import build_parser


def test_online_key_defaults_relative_to_selected_data_directory() -> None:
    args = build_parser().parse_args(["--data-dir", "D:/private-voice-data"])

    key_file = (
        args.elevenlabs_key_file
        if args.elevenlabs_key_file is not None
        else args.data_dir / "secrets" / "elevenlabs-api-key"
    )

    assert key_file == Path("D:/private-voice-data/secrets/elevenlabs-api-key")
