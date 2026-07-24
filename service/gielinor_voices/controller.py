from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from contextlib import closing
from pathlib import Path
from typing import Callable

import numpy as np

from .casting import CastingDirector, Performance
from .engine import (
    CompleteVoiceEngine,
    QwenVoiceEngine,
    StreamingVoiceEngine,
    VoiceEngine,
)
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
        self._audio_lock = threading.Lock()
        self._output_stream: object | None = None
        self._state = "loading"
        self._last_error = ""
        self._last_first_audio_ms: int | None = None
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
                "lastFirstAudioMs": self._last_first_audio_ms,
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
        started_at = time.monotonic()
        performance = self._director.performance_for(request)
        cache_path = self._cache_path(request, performance, self._engine.identity)
        import soundfile as sf

        if cache_path.exists():
            waveform, sample_rate = sf.read(cache_path, dtype="float32")
            waveform = np.asarray(waveform, dtype=np.float32).reshape(-1)
            os.utime(cache_path, None)
            if not self._is_current(ticket):
                return
            import sounddevice as sd

            self._record_first_audio(started_at)
            sd.play(waveform * request.volume, sample_rate, blocking=True)
            return

        if isinstance(self._engine, StreamingVoiceEngine):
            self._perform_streamed(
                ticket,
                request,
                performance,
                cache_path,
                started_at,
            )
            return

        if not isinstance(self._engine, CompleteVoiceEngine):
            raise RuntimeError("The selected voice engine cannot create audio")
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

        self._record_first_audio(started_at)
        sd.play(waveform * request.volume, sample_rate, blocking=True)

    def _perform_streamed(
        self,
        ticket: int,
        request: SpeechRequest,
        performance: Performance,
        cache_path: Path,
        started_at: float,
    ) -> None:
        assert isinstance(self._engine, StreamingVoiceEngine)
        import sounddevice as sd
        import soundfile as sf

        chunks: list[np.ndarray] = []
        first_chunk = True
        output_stream = sd.OutputStream(
            samplerate=self._engine.sample_rate,
            channels=1,
            dtype="float32",
            latency="low",
        )
        try:
            output_stream.start()
            with self._audio_lock:
                if not self._is_current(ticket):
                    output_stream.close()
                    return
                self._output_stream = output_stream
            with closing(self._engine.stream(request.text, performance)) as audio:
                for chunk in audio:
                    if not self._is_current(ticket):
                        return
                    clean = np.asarray(chunk, dtype=np.float32).reshape(-1)
                    if clean.size == 0 or not np.isfinite(clean).all():
                        raise RuntimeError("The streaming voice engine returned invalid audio")
                    chunks.append(clean)
                    if first_chunk:
                        self._record_first_audio(started_at)
                        first_chunk = False
                    output_stream.write(clean * request.volume)
        except Exception:
            if self._is_current(ticket):
                raise
            return
        finally:
            with self._audio_lock:
                if self._output_stream is output_stream:
                    self._output_stream = None
            try:
                output_stream.close()
            except Exception:
                pass

        if not self._is_current(ticket) or not chunks:
            return
        waveform = np.concatenate(chunks)
        temporary = cache_path.with_suffix(".tmp.wav")
        sf.write(
            temporary,
            waveform,
            self._engine.sample_rate,
            subtype="PCM_16",
        )
        temporary.replace(cache_path)
        self._trim_cache()

    def _record_first_audio(self, started_at: float) -> None:
        elapsed_ms = max(0, round((time.monotonic() - started_at) * 1000))
        with self._condition:
            self._last_first_audio_ms = elapsed_ms
        LOGGER.info("First audio was ready in %s ms", elapsed_ms)

    def _stop_audio(self) -> None:
        with self._audio_lock:
            output_stream = self._output_stream
            self._output_stream = None
        if output_stream is not None:
            try:
                output_stream.abort()  # type: ignore[attr-defined]
                output_stream.close()  # type: ignore[attr-defined]
            except Exception:
                pass
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
