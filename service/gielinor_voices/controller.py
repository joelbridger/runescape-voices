from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Callable

import numpy as np

from .casting import CastingDirector, Performance
from .engine import QwenVoiceEngine, VoiceEngine
from .models import SpeechRequest


LOGGER = logging.getLogger(__name__)


class SpeechController:
    def __init__(
        self,
        cache_dir: Path,
        engine_factory: Callable[[], VoiceEngine] = QwenVoiceEngine,
        cache_limit_bytes: int = 4 * 1024 * 1024 * 1024,
    ) -> None:
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._engine_factory = engine_factory
        self._cache_limit_bytes = cache_limit_bytes
        self._director = CastingDirector()
        self._condition = threading.Condition()
        self._pending: tuple[int, SpeechRequest] | None = None
        self._active: SpeechRequest | None = None
        self._generation = 0
        self._stopping = False
        self._engine: VoiceEngine | None = None
        self._state = "loading"
        self._last_error = ""
        self._thread = threading.Thread(target=self._run, name="voice-worker", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        with self._condition:
            self._stopping = True
            self._generation += 1
            self._pending = None
            self._condition.notify_all()
        self._stop_audio()
        self._thread.join(timeout=5)

    def submit(self, request: SpeechRequest) -> bool:
        with self._condition:
            if (
                not request.is_dialogue
                and (
                    (self._active is not None and self._active.is_dialogue)
                    or (self._pending is not None and self._pending[1].is_dialogue)
                )
            ):
                return False
            self._generation += 1
            ticket = self._generation
            self._pending = (ticket, request)
            self._condition.notify_all()
        self._stop_audio()
        return True

    def cancel(self) -> None:
        with self._condition:
            self._generation += 1
            self._pending = None
            self._condition.notify_all()
        self._stop_audio()

    def status(self) -> dict[str, object]:
        with self._condition:
            return {
                "status": self._state,
                "engine": self._engine.identity if self._engine else None,
                "queued": self._pending is not None,
                "speaking": self._active is not None,
                "lastError": self._last_error or None,
            }

    def _run(self) -> None:
        try:
            self._engine = self._engine_factory()
            with self._condition:
                self._state = "ready"
                self._last_error = ""
        except Exception as exception:
            LOGGER.exception("The local voice model could not start")
            with self._condition:
                self._state = "error"
                self._last_error = str(exception)[:240]
            return

        while True:
            with self._condition:
                while self._pending is None and not self._stopping:
                    self._condition.wait()
                if self._stopping:
                    return
                ticket, request = self._pending
                self._pending = None
                self._active = request
            try:
                self._perform(ticket, request)
            except Exception as exception:
                LOGGER.exception("A line could not be performed")
                with self._condition:
                    self._last_error = str(exception)[:240]
            finally:
                with self._condition:
                    if self._active == request:
                        self._active = None

    def _perform(self, ticket: int, request: SpeechRequest) -> None:
        assert self._engine is not None
        performance = self._director.performance_for(request)
        cache_path = self._cache_path(request, performance, self._engine.identity)
        import soundfile as sf

        if cache_path.exists():
            waveform, sample_rate = sf.read(cache_path, dtype="float32")
            waveform = np.asarray(waveform, dtype=np.float32).reshape(-1)
            os.utime(cache_path, None)
        else:
            waveform, sample_rate = self._engine.generate(request.text, performance)
            if not self._is_current(ticket):
                return
            temporary = cache_path.with_suffix(".tmp.wav")
            sf.write(temporary, waveform, sample_rate, subtype="PCM_16")
            temporary.replace(cache_path)
            self._trim_cache()
        if not self._is_current(ticket):
            return
        import sounddevice as sd

        sd.play(waveform * request.volume, sample_rate, blocking=True)

    @staticmethod
    def _stop_audio() -> None:
        try:
            import sounddevice as sd

            sd.stop()
        except (ImportError, OSError):
            # Startup diagnostics will report a missing audio device. Cancellation
            # itself must remain safe while the service is still loading.
            return

    def _is_current(self, ticket: int) -> bool:
        with self._condition:
            return ticket == self._generation and not self._stopping

    def _cache_path(
        self,
        request: SpeechRequest,
        performance: Performance,
        engine_identity: str,
    ) -> Path:
        cache_value = json.dumps(
            {
                "engine": engine_identity,
                "speaker": performance.speaker,
                "instruction": performance.instruction,
                "speakerKey": request.speaker_key,
                "text": request.text,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(cache_value.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{digest}.wav"

    def _trim_cache(self) -> None:
        files = [path for path in self._cache_dir.glob("*.wav") if path.is_file()]
        total = sum(path.stat().st_size for path in files)
        if total <= self._cache_limit_bytes:
            return
        for path in sorted(files, key=lambda item: item.stat().st_mtime):
            size = path.stat().st_size
            path.unlink(missing_ok=True)
            total -= size
            if total <= self._cache_limit_bytes:
                break
