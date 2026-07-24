from __future__ import annotations

import hmac
import json
import logging
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .controller import SpeechController
from .models import SpeechRequest


LOGGER = logging.getLogger(__name__)
MAX_BODY_BYTES = 8_192


class VoiceHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(
        self,
        address: tuple[str, int],
        token: str,
        controller: SpeechController,
    ) -> None:
        if address[0] not in {"127.0.0.1", "localhost"}:
            raise ValueError("the voice service may listen only on this PC")
        self.token = token
        self.controller = controller
        super().__init__(address, VoiceRequestHandler)


class VoiceRequestHandler(BaseHTTPRequestHandler):
    server: VoiceHTTPServer

    def do_GET(self) -> None:
        if self.path != "/health":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        self._json(HTTPStatus.OK, self.server.controller.status())

    def do_POST(self) -> None:
        if not self._authorized():
            self._json(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
            return
        if self.path == "/v1/cancel":
            self.server.controller.cancel()
            self._json(HTTPStatus.ACCEPTED, {"status": "cancelled"})
            return
        if self.path != "/v1/speak":
            self._json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        try:
            value = self._read_json()
            request = SpeechRequest.from_json(value)
            accepted = self.server.controller.submit(request)
        except ValueError as exception:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(exception)})
            return
        self._json(
            HTTPStatus.ACCEPTED,
            {"status": "queued" if accepted else "ignored"},
        )

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.debug("%s - %s", self.address_string(), format % args)

    def _authorized(self) -> bool:
        header = self.headers.get("Authorization", "")
        prefix = "Bearer "
        if not header.startswith(prefix):
            return False
        return hmac.compare_digest(header[len(prefix) :], self.server.token)

    def _read_json(self) -> Any:
        length_header = self.headers.get("Content-Length")
        if length_header is None:
            raise ValueError("content length is required")
        try:
            length = int(length_header)
        except ValueError as exception:
            raise ValueError("invalid content length") from exception
        if length < 0 or length > MAX_BODY_BYTES:
            raise ValueError("request is too large")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exception:
            raise ValueError("request is not valid JSON") from exception

    def _json(self, status: HTTPStatus, value: dict[str, object]) -> None:
        body = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.send_response(status.value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

