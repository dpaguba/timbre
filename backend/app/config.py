"""Application configuration.

Every setting can be overridden with an environment variable, so the app runs
locally without code changes.

Environment variables:
    TIMBRE_DATA_DIR
        Uploads and generated transcripts. Defaults to ``backend/data`` in a
        source checkout and to the per-user application directory in a
        packaged build.
    TIMBRE_MODEL_DIR
        Where faster-whisper caches models. Defaults to the Hugging Face cache
        so models are shared with other projects.
    TIMBRE_MODEL
        Default model name. Smaller is faster, larger is more accurate.
    TIMBRE_DEVICE
        ``auto``, ``cpu`` or ``cuda``.
    TIMBRE_COMPUTE_TYPE
        Precision passed to ctranslate2. ``int8`` is the default on CPU
        because most processors, Apple Silicon included, cannot do efficient
        float16 and would silently upcast to float32 and run several times
        slower. CUDA defaults to float16.
    TIMBRE_TOKEN
        Bearer token every request must carry. The desktop shell generates a
        random one per launch, which is a guarantee no Origin header can make.
    TIMBRE_DEV
        Set to ``1`` to accept the Vite dev server origin, the only situation
        where a cross-origin request is legitimate.
    TIMBRE_MAX_UPLOAD_BYTES, TIMBRE_MAX_JOB_BYTES
        Upload guards. They turn a disk-filling mistake into a clear error
        rather than stopping an attacker; raise them for genuinely large work.
    TIMBRE_RETENTION_DAYS
        Days before old uploads and transcripts are deleted, ``0`` to keep
        everything. Media files are large and nothing else removes them.
    TIMBRE_PRUNE_INTERVAL_SECONDS
        How often a running server sweeps. Pruning only at startup never fires
        on a machine that leaves the app open.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_ID = "one.timbre.app"


def _user_data_dir() -> Path:
    """The per-user directory the platform expects an application to write to.

    Matches the desktop shell's bundle identifier, so the server's data sits
    beside the window state and settings the shell writes rather than in a
    second place under a different name.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        return Path(base or Path.home() / "AppData" / "Local") / APP_ID
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_ID
    base = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share"
    return Path(base) / "timbre"


def _data_dir() -> Path:
    """Where uploads and generated transcripts are written.

    A source checkout keeps its data in the working tree, which is convenient
    and easy to delete. A packaged build must not: everything beside the frozen
    executable lives inside the application bundle, which is read-only when the
    app is launched straight from a downloaded disk image, is covered by the
    code signature, and is replaced wholesale on the next update.
    """
    override = os.environ.get("TIMBRE_DATA_DIR")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        return _user_data_dir() / "data"
    return Path(__file__).resolve().parent.parent / "data"


DATA_DIR = _data_dir()
UPLOAD_DIR = DATA_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "outputs"

MODEL_DIR = os.environ.get("TIMBRE_MODEL_DIR") or None
DEFAULT_MODEL = os.environ.get("TIMBRE_MODEL", "small")
DEVICE = os.environ.get("TIMBRE_DEVICE", "auto")

_DEFAULT_COMPUTE = "float16" if DEVICE == "cuda" else "int8"
COMPUTE_TYPE = os.environ.get("TIMBRE_COMPUTE_TYPE", _DEFAULT_COMPUTE)

AUTH_TOKEN = os.environ.get("TIMBRE_TOKEN") or None

LOCAL_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

DEV_MODE = os.environ.get("TIMBRE_DEV", "").lower() in {"1", "true", "yes"}

DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _frontend_dist() -> Path:
    """Where the built SPA lives.

    Under PyInstaller the source tree is gone and everything sits beside the
    executable, so the repository-relative path does not apply.
    """
    override = os.environ.get("TIMBRE_FRONTEND_DIST")
    if override:
        return Path(override)
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "frontend"
    return Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


FRONTEND_DIST = _frontend_dist()


def _int_env(name: str, default: int) -> int:
    """Read an integer setting.

    Fails with the variable name rather than a bare ValueError traceback from
    somewhere inside the import.
    """
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        unit = "days" if "DAYS" in name else "bytes"
        raise SystemExit(f"{name} must be a whole number of {unit}, got {raw!r}") from None


MAX_UPLOAD_BYTES = _int_env("TIMBRE_MAX_UPLOAD_BYTES", 4 * 1024 ** 3)
MAX_JOB_BYTES = _int_env("TIMBRE_MAX_JOB_BYTES", 16 * 1024 ** 3)
DATA_RETENTION_DAYS = _int_env("TIMBRE_RETENTION_DAYS", 7)
PRUNE_INTERVAL_SECONDS = _int_env("TIMBRE_PRUNE_INTERVAL_SECONDS", 6 * 3600)


def ensure_dirs() -> None:
    """Create runtime directories if they do not exist yet."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
