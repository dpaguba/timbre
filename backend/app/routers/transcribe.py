"""HTTP API for uploading media, running jobs and downloading transcripts."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..config import AUTH_TOKEN, MAX_JOB_BYTES, MAX_UPLOAD_BYTES, UPLOAD_DIR
from ..jobs import JobManager
from ..languages import LANGUAGES, MODELS
from ..media import ffmpeg_available
from ..models import JobStatus, OutputFormat, TranscribeOptions
from ..models_store import store

_LANGUAGE_CODES = {lang["code"] for lang in LANGUAGES}

router = APIRouter(prefix="/api", tags=["transcribe"])
manager = JobManager()

_MEDIA_TYPE = {
    OutputFormat.TXT: "text/plain",
    OutputFormat.MARKDOWN: "text/markdown",
    OutputFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "ffmpeg": ffmpeg_available()}


@router.get("/languages")
def languages() -> dict:
    """List the languages, models and upload limits the frontend needs.

    The limits ride along here because the frontend already fetches this once
    at boot. Without them a browser could only discover a limit by uploading
    gigabytes and reading the 413 that comes back afterwards.
    """
    return {
        "languages": LANGUAGES,
        "models": MODELS,
        "limits": {
            "max_upload_bytes": MAX_UPLOAD_BYTES,
            "max_job_bytes": MAX_JOB_BYTES,
        },
    }


def _validate_options(opts: TranscribeOptions) -> None:
    """Guard the two fields that reach outside the process.

    faster-whisper treats any model string containing a slash as a Hugging Face
    repository id and downloads it, so the allowlist the UI already offers is
    enforced here as well.
    """
    if opts.model not in MODELS:
        raise HTTPException(status_code=422, detail=f"Unknown model. Choose one of: {', '.join(MODELS)}")

    unknown = [code for code in opts.languages if code not in _LANGUAGE_CODES]
    if unknown:
        raise HTTPException(status_code=422, detail=f"Unknown language code(s): {', '.join(unknown)}")


def _gb(num_bytes: int) -> str:
    """Render a byte limit the way a person would say it."""
    for threshold, unit in ((1024 ** 3, "GB"), (1024 ** 2, "MB"), (1024, "KB")):
        if num_bytes >= threshold:
            value = num_bytes / threshold
            return f"{value:.0f} {unit}" if value >= 10 else f"{value:.1f} {unit}"
    return f"{num_bytes} bytes"


def _abandon(job_id: str, job_dir: Path) -> None:
    """Drop a job that never started, along with whatever it wrote."""
    shutil.rmtree(job_dir, ignore_errors=True)
    manager.discard(job_id)


class _TooLarge(Exception):
    """Raised when an upload exceeds the configured size guard."""


def _copy_bounded(src, dst: Path, per_file_limit: int, remaining_job_budget: int) -> int:
    """Stream `src` into `dst`, stopping if either limit would be crossed.

    This is the second line of defence. Starlette has already buffered the whole
    multipart body into a spooled temporary file before the endpoint runs, so the
    early Content-Length check in `LimitUploadSizeMiddleware` is what actually
    keeps a huge upload off the disk. This guard stops the second copy, and
    catches chunked requests that arrive without a Content-Length.
    """
    chunk_size = 1024 * 1024
    written = 0
    with dst.open("wb") as fh:
        while chunk := src.read(chunk_size):
            written += len(chunk)
            if written > per_file_limit:
                raise _TooLarge(
                    f"{dst.name} is larger than the {_gb(per_file_limit)} per-file limit. "
                    "Raise TIMBRE_MAX_UPLOAD_BYTES to allow it."
                )
            if written > remaining_job_budget:
                raise _TooLarge(
                    f"This batch is larger than the {_gb(MAX_JOB_BYTES)} total limit. "
                    "Upload fewer files at once, or raise TIMBRE_MAX_JOB_BYTES."
                )
            fh.write(chunk)
    return written


@router.get("/models")
def models_state() -> dict:
    """What is on disk, what is downloading, and how big each one is."""
    return {"models": store.list_models()}


@router.post("/models/{name}/download")
def download_model(name: str) -> dict:
    try:
        job = store.start_download(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown model: {name}") from exc
    return {"model": job.model, "state": job.state}


@router.post("/models/{name}/cancel")
def cancel_model(name: str) -> dict:
    store.cancel(name)
    return {"model": name, "state": "cancelling"}


@router.delete("/models/{name}")
def remove_model(name: str) -> dict:
    try:
        freed = store.remove(name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown model: {name}") from exc
    return {"model": name, "freed_bytes": freed}


@router.post("/jobs", response_model=JobStatus)
def create_job(
    files: list[UploadFile] = File(...),
    options: str = Form(...),
) -> JobStatus:
    """Accept any number of media files plus a JSON `options` blob.

    Deliberately synchronous: copying gigabytes runs in FastAPI's threadpool
    instead of blocking the event loop, so status polling keeps responding
    while a large upload is still arriving.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    try:
        opts = TranscribeOptions(**json.loads(options))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid options: {exc}") from exc

    _validate_options(opts)

    job = manager.create_job([], opts)
    job_upload_dir = UPLOAD_DIR / job.job_id
    job_upload_dir.mkdir(parents=True, exist_ok=True)

    declared_total = sum(upload.size or 0 for upload in files)
    if declared_total > MAX_JOB_BYTES:
        manager.discard(job.job_id)
        raise HTTPException(
            status_code=413,
            detail=(
                f"This batch is larger than the {_gb(MAX_JOB_BYTES)} total limit. "
                "Upload fewer files at once, or raise TIMBRE_MAX_JOB_BYTES."
            ),
        )

    saved: list[Path] = []
    total_bytes = 0
    for index, upload in enumerate(files):
        safe_name = Path(upload.filename or "file").name
        if safe_name in ("", ".", ".."):
            safe_name = f"file_{index:03d}"
        slot = job_upload_dir / f"{index:03d}"
        slot.mkdir(parents=True, exist_ok=True)
        dst = slot / safe_name
        try:
            written = _copy_bounded(upload.file, dst, MAX_UPLOAD_BYTES, MAX_JOB_BYTES - total_bytes)
        except _TooLarge as exc:
            _abandon(job.job_id, job_upload_dir)
            raise HTTPException(status_code=413, detail=str(exc)) from exc
        except Exception as exc:
            _abandon(job.job_id, job_upload_dir)
            raise HTTPException(status_code=400, detail=f"Could not store {safe_name}: {exc}") from exc
        total_bytes += written
        saved.append(dst)

    job.sources = saved
    from ..models import FileProgress

    job.status.files = [FileProgress(filename=p.name) for p in saved]
    manager.start(job.job_id)
    return job.status


class LocalJobRequest(BaseModel):
    """Paths the desktop shell picked, plus the usual options."""

    paths: list[str]
    options: TranscribeOptions


@router.post("/jobs/local", response_model=JobStatus)
def create_local_job(request: LocalJobRequest) -> JobStatus:
    """Start a job from files already on this machine.

    The desktop app has real paths, so copying a four gigabyte recording
    through multipart HTTP into a process on the same disk is pure waste. The
    browser build keeps using /jobs, which has no path to give.

    The endpoint exists only when a token is configured. Only the desktop shell
    can supply a trustworthy path; without that gate, any page on the machine
    could ask the server to read an arbitrary file.
    """
    if AUTH_TOKEN is None:
        raise HTTPException(status_code=404, detail="Not found.")

    if not request.paths:
        raise HTTPException(status_code=400, detail="No files given.")

    _validate_options(request.options)

    sources: list[Path] = []
    for raw in request.paths:
        path = Path(raw).expanduser()
        if not path.is_file():
            raise HTTPException(status_code=400, detail=f"Not a file: {raw}")
        sources.append(path.resolve())

    job = manager.create_job(sources, request.options)
    manager.start(job.job_id)
    return job.status


@router.get("/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.status


@router.get("/jobs/{job_id}/download")
def download(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job.output_path is None or not job.output_path.exists():
        raise HTTPException(status_code=409, detail="Transcript is not ready yet.")
    media_type = _MEDIA_TYPE[job.options.output_format]
    return FileResponse(job.output_path, media_type=media_type, filename=job.output_path.name)
