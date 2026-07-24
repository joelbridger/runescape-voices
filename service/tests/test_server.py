from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from gielinor_voices.server import VoiceHTTPServer


class FakeController:
    def __init__(self) -> None:
        self.request = None
        self.cancelled = False

    def status(self) -> dict[str, object]:
        return {"status": "ready"}

    def submit(self, request: object) -> bool:
        self.request = request
        return True

    def cancel(self) -> None:
        self.cancelled = True


def test_server_is_authenticated_and_loopback_only() -> None:
    controller = FakeController()
    server = VoiceHTTPServer(("127.0.0.1", 0), "x" * 48, controller)  # type: ignore[arg-type]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        body = json.dumps(
            {
                "speakerKey": "npc:zanik",
                "speakerName": "Zanik",
                "text": "Hello.",
                "kind": "npc-dialogue",
                "sequence": 1,
                "volume": 0.8,
            }
        ).encode()
        unauthenticated = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/speak",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            urllib.request.urlopen(unauthenticated)
            raise AssertionError("unauthenticated request unexpectedly succeeded")
        except urllib.error.HTTPError as error:
            assert error.code == 401

        authenticated = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/speak",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {'x' * 48}",
            },
        )
        with urllib.request.urlopen(authenticated) as response:
            assert response.status == 202
        assert controller.request is not None
    finally:
        server.shutdown()
        server.server_close()
        thread.join()

