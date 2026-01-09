"""What is on disk, and how to get more of it.

Models are the one thing this app cannot ship: `small` alone is roughly 500 MB
and `large-v3` is 3 GB. So the first run downloads one, and this module is what
the onboarding screen talks to.

`APPROX_BYTES` holds the download sizes of the int8 CTranslate2 conversions
faster-whisper fetches. They are shown before a download starts, so they are
deliberately rounded rather than precise.
"""
from __future__ import annotations

import shutil
import threading
from dataclasses import dataclass, field
from pathlib import Path

from .config import MODEL_DIR
from .languages import MODELS

APPROX_BYTES = {
    "tiny": 75 * 1024 ** 2,
    "base": 145 * 1024 ** 2,
    "small": 480 * 1024 ** 2,
    "medium": 1_500 * 1024 ** 2,
    "large-v3": 3_000 * 1024 ** 2,
}

_REPO = {name: f"Systran/faster-whisper-{name}" for name in MODELS}


def _cache_root() -> Path:
    if MODEL_DIR:
        return Path(MODEL_DIR)
    return Path.home() / ".cache" / "huggingface" / "hub"


def _model_dir(name: str) -> Path:
    return _cache_root() / f"models--{_REPO[name].replace('/', '--')}"


def _dir_size(path: Path) -> int:
    """Bytes actually occupied.

    The Hugging Face cache keeps one copy in `blobs/` and points at it from
    `snapshots/` with symlinks. Following those links counts every model twice,
    which turned a 3 GB download into a reported 5.9 GB.
    """
    if not path.is_dir():
        return 0
    total = 0
    for entry in path.rglob("*"):
        if entry.is_symlink() or not entry.is_file():
            continue
        try:
            total += entry.stat().st_size
        except OSError:
            continue
    return total


@dataclass
class Download:
    """Progress of one model download, shared with the polling client."""

    model: str
    state: str = "running"  # running | done | error
    downloaded: int = 0
    total: int = 0
    error: str | None = None
    cancel: threading.Event = field(default_factory=threading.Event)


class ModelStore:
    def __init__(self) -> None:
        self._downloads: dict[str, Download] = {}
        self._lock = threading.Lock()

    def list_models(self) -> list[dict]:
        out = []
        for name in MODELS:
            path = _model_dir(name)
            size = _dir_size(path)
            with self._lock:
                active = self._downloads.get(name)
            out.append(
                {
                    "name": name,
                    "installed": size > 0 and active is None,
                    "size_bytes": size,
                    "approx_bytes": APPROX_BYTES.get(name, 0),
                    "download": None
                    if active is None
                    else {
                        "state": active.state,
                        "downloaded": active.downloaded,
                        "total": active.total,
                        "error": active.error,
                    },
                }
            )
        return out

    def start_download(self, name: str) -> Download:
        if name not in MODELS:
            raise KeyError(name)
        with self._lock:
            existing = self._downloads.get(name)
            if existing and existing.state == "running":
                return existing
            job = Download(model=name, total=APPROX_BYTES.get(name, 0))
            self._downloads[name] = job

        threading.Thread(target=self._run, args=(job,), daemon=True).start()
        return job

    def cancel(self, name: str) -> None:
        with self._lock:
            job = self._downloads.get(name)
        if job:
            job.cancel.set()

    def remove(self, name: str) -> int:
        """Delete a downloaded model, returning the bytes freed."""
        if name not in MODELS:
            raise KeyError(name)
        path = _model_dir(name)
        freed = _dir_size(path)
        shutil.rmtree(path, ignore_errors=True)
        with self._lock:
            self._downloads.pop(name, None)
        return freed

    def _run(self, job: Download) -> None:
        """Fetch the model, reporting progress by watching the cache grow.

        huggingface_hub does expose per-file callbacks, but they change between
        versions and say nothing about files still queued. Measuring the
        directory is version-proof and is what the user actually cares about.
        """
        stop = threading.Event()

        def watch() -> None:
            path = _model_dir(job.model)
            while not stop.wait(0.5):
                job.downloaded = _dir_size(path)

        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        try:
            from faster_whisper import WhisperModel

            WhisperModel(job.model, device="cpu", compute_type="int8", download_root=MODEL_DIR)
            if job.cancel.is_set():
                job.state = "error"
                job.error = "Cancelled."
            else:
                job.state = "done"
                job.downloaded = job.total = _dir_size(_model_dir(job.model))
        except Exception as exc:  # noqa: BLE001 - reported to the client verbatim
            job.state = "error"
            job.error = str(exc)
        finally:
            stop.set()


store = ModelStore()
