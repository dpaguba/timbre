"""Removal of old runtime data.

Uploads are media files and transcripts accumulate beside them. Nothing else in
the app deletes either, so a machine that transcribes regularly fills its disk
and the failure surfaces as an unrelated write error somewhere else. This runs
once at startup and removes job directories older than the retention window.
"""
from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

from .config import DATA_RETENTION_DAYS, OUTPUT_DIR, UPLOAD_DIR

log = logging.getLogger(__name__)


def _newest_mtime(entry: Path) -> float:
    """Most recent mtime anywhere inside `entry`.

    A directory's own mtime only changes when a direct child is added or
    removed, so `uploads/<job>/` keeps the timestamp it had at creation while
    gigabytes are still being written into `wav/` below it. Keying on the
    directory alone would let a periodic sweep delete the sources of a job that
    is still running.
    """
    try:
        newest = entry.stat().st_mtime
    except OSError:
        return 0.0
    if entry.is_dir():
        for child in entry.rglob("*"):
            try:
                newest = max(newest, child.stat().st_mtime)
            except OSError:
                continue
    return newest


def _prune(directory: Path, cutoff: float, protected: set[str] | None = None) -> tuple[int, int]:
    """Delete entries in `directory` untouched since `cutoff`."""
    removed = 0
    freed = 0
    if not directory.is_dir():
        return removed, freed

    protected = protected or set()
    for entry in directory.iterdir():
        try:
            if entry.name in protected:
                continue
            if _newest_mtime(entry) >= cutoff:
                continue
            if entry.is_dir():
                size = sum(f.stat().st_size for f in entry.rglob("*") if f.is_file())
            else:
                size = entry.stat().st_size
            if entry.is_dir():
                shutil.rmtree(entry)
            else:
                entry.unlink()
            removed += 1
            freed += size
        except OSError as exc:
            log.warning("could not remove %s: %s", entry, exc)
    return removed, freed


def prune_old_data(retention_days: int | None = None, protected: set[str] | None = None) -> tuple[int, int]:
    """Remove uploads and outputs older than the retention window.

    Returns the number of entries removed and the bytes freed. A retention of 0
    disables pruning entirely.
    """
    days = DATA_RETENTION_DAYS if retention_days is None else retention_days
    if days <= 0:
        return 0, 0

    cutoff = time.time() - days * 86400
    removed = 0
    freed = 0
    for directory in (UPLOAD_DIR, OUTPUT_DIR):
        r, f = _prune(directory, cutoff, protected)
        removed += r
        freed += f

    if removed:
        log.info("housekeeping removed %d old item(s), freed %.1f MB", removed, freed / 1024 / 1024)
    return removed, freed
