"""Transcription engine built on faster-whisper (free, fully offline).

The engine is intentionally isolated behind a small interface so it can be
stubbed in tests without importing the heavy ML dependency.
"""
from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from .config import COMPUTE_TYPE, DEVICE, MODEL_DIR
from .media import extract_wav, probe_duration
from .models import FileResult, Segment, TranscribeOptions

ProgressFn = Callable[[float], None]
"""Progress callback. Receives a value in 0..1 for the current file."""


class WhisperEngine:
    """Thin wrapper around faster-whisper with lazy, cached model loading."""

    def __init__(self) -> None:
        self._models: dict[str, object] = {}
        self._model_lock = threading.Lock()

    def _get_model(self, size: str):
        """Load a model, keeping only the most recently used one.

        large-v3 is roughly 1.5 GB in int8, so somebody trying several sizes
        would otherwise hold all of them for the life of the process. The lock
        stops two jobs building the same model twice. faster-whisper is
        imported lazily so the API can start, and the tests can run, without it
        installed.
        """
        with self._model_lock:
            if size not in self._models:
                from faster_whisper import WhisperModel

                self._models.clear()
                self._models[size] = WhisperModel(
                    size, device=DEVICE, compute_type=COMPUTE_TYPE, download_root=MODEL_DIR
                )
            return self._models[size]

    def transcribe_file(
        self,
        src: Path,
        work_wav: Path,
        options: TranscribeOptions,
        on_progress: ProgressFn | None = None,
    ) -> FileResult:
        """Transcribe one media file into a FileResult.

        Language handling:
          * 0 languages selected  -> Whisper auto-detects (whole file).
          * 1 language selected    -> forced to that language.
          * >1 selected -> multilingual decoding, which detects the language on
            every window internally. The library does not report which language
            it chose per segment, so the selection widens detection rather than
            constraining it.

        Every segment carries the language detected for the file as a whole.
        faster-whisper's Segment has no language field, checked against 1.2.x,
        so even under multilingual decoding that file-level value is the only
        one the library reports.
        """
        extract_wav(src, work_wav)
        duration = probe_duration(src) or probe_duration(work_wav)
        model = self._get_model(options.model)

        language, multilingual = self._resolve_language_mode(options)

        segments_iter, info = model.transcribe(
            str(work_wav),
            language=language,
            multilingual=multilingual,
            vad_filter=True,
            beam_size=5,
        )

        file_language = getattr(info, "language", None)
        collected: list[Segment] = []
        for seg in segments_iter:
            collected.append(
                Segment(start=float(seg.start), end=float(seg.end), text=seg.text, language=file_language)
            )
            if on_progress and duration > 0:
                on_progress(min(seg.end / duration, 1.0))

        if on_progress:
            on_progress(1.0)

        return FileResult(
            filename=src.name,
            detected_language=getattr(info, "language", None),
            duration=duration,
            segments=collected,
        )

    @staticmethod
    def _resolve_language_mode(options: TranscribeOptions) -> tuple[str | None, bool]:
        langs = options.languages
        if len(langs) == 1:
            return langs[0], False
        if len(langs) > 1 or options.multilingual:
            return None, True
        return None, False
