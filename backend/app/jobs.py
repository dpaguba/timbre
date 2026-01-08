"""In-memory job manager.

Because Timbre runs locally for a single user, an in-memory registry with a
background worker thread is the simplest thing that works. No database, no
external queue. State is lost on restart, which is fine for a local tool.
"""
from __future__ import annotations

import logging
import shutil
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .config import OUTPUT_DIR, UPLOAD_DIR
from .exporters import export
from .models import (
    FileProgress,
    FileResult,
    JobState,
    JobStatus,
    TranscribeOptions,
)
from .transcription import WhisperEngine


@dataclass
class Job:
    job_id: str
    options: TranscribeOptions
    sources: list[Path]
    status: JobStatus
    results: list[FileResult] = field(default_factory=list)
    output_path: Path | None = None


log = logging.getLogger(__name__)


class JobManager:
    """Owns job lifecycle and runs transcription on a background thread.

    Exactly one job transcribes at a time. Transcription saturates every core,
    so running several at once is slower than running them in turn and
    multiplies peak memory by the number of jobs. The QUEUED state already
    models the wait for the user.
    """

    def __init__(self, engine: WhisperEngine | None = None) -> None:
        self._engine = engine or WhisperEngine()
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._slot = threading.Semaphore(1)

    def create_job(self, sources: list[Path], options: TranscribeOptions) -> Job:
        job_id = uuid.uuid4().hex[:12]
        status = JobStatus(
            job_id=job_id,
            state=JobState.QUEUED,
            options=options,
            files=[FileProgress(filename=p.name) for p in sources],
        )
        job = Job(job_id=job_id, options=options, sources=sources, status=status)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def active_job_ids(self) -> list[str]:
        """Ids of jobs housekeeping must not touch."""
        with self._lock:
            return [
                job_id
                for job_id, job in self._jobs.items()
                if job.status.state in (JobState.QUEUED, JobState.RUNNING)
            ]

    def discard(self, job_id: str) -> None:
        """Forget a job that never started, so a failed upload leaves nothing."""
        with self._lock:
            self._jobs.pop(job_id, None)

    def start(self, job_id: str) -> None:
        thread = threading.Thread(target=self._run, args=(job_id,), daemon=True)
        thread.start()

    def _run(self, job_id: str) -> None:
        """Wait for a free slot before claiming to be running.

        The status the user sees then matches what the machine is actually
        doing.
        """
        job = self.get(job_id)
        if job is None:
            return
        with self._slot:
            self._run_locked(job, job_id)

    def _run_locked(self, job: Job, job_id: str) -> None:
        """Transcribe every source in the job, then write one document.

        Creating the working directory happens inside the try block on purpose:
        a failure there, such as a full disk or a read-only volume, would
        otherwise escape into the thread and leave the job RUNNING forever.

        A job whose every file failed is reported as an error rather than done.
        Reporting DONE would hand back a green tick and an empty transcript,
        which is what the two most common first-run problems look like: no
        network for the model download, and a broken decoder.
        """
        job.status.state = JobState.RUNNING
        work_dir = UPLOAD_DIR / job_id / "wav"
        try:
            work_dir.mkdir(parents=True, exist_ok=True)
            for idx, src in enumerate(job.sources):
                progress = job.status.files[idx]
                progress.state = JobState.RUNNING
                try:
                    result = self._engine.transcribe_file(
                        src,
                        work_dir / f"{idx:03d}_{src.stem}.wav",
                        job.options,
                        on_progress=lambda p, fp=progress: setattr(fp, "progress", p),
                    )
                    job.results.append(result)
                    progress.detected_language = result.detected_language
                    progress.progress = 1.0
                    progress.state = JobState.DONE
                except Exception as exc:
                    log.exception("job %s: file %s failed", job_id, src.name)
                    progress.state = JobState.ERROR
                    progress.error = str(exc)

            if job.sources and not job.results:
                first_error = next((f.error for f in job.status.files if f.error), None)
                job.status.state = JobState.ERROR
                job.status.error = first_error or "Every file failed to transcribe."
                return

            job.output_path = self._write_output(job)
            job.status.state = JobState.DONE
        except Exception as exc:
            log.exception("job %s failed", job_id)
            job.status.state = JobState.ERROR
            job.status.error = str(exc)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)

    def _write_output(self, job: Job) -> Path:
        out_name = f"transcript_{job.job_id}.{job.options.output_format.value}"
        dst = OUTPUT_DIR / out_name
        return export(job.results, job.options, dst)
