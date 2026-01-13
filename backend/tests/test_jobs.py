from __future__ import annotations

import os
import time
from pathlib import Path

from app import jobs as jobs_module
from app.jobs import JobManager
from app.models import FileResult, JobState, OutputFormat, Segment, TranscribeOptions


class StubEngine:
    """Engine replacement that skips ffmpeg/whisper and returns canned text."""

    def transcribe_file(self, src: Path, work_wav: Path, options, on_progress=None):
        if on_progress:
            on_progress(0.5)
            on_progress(1.0)
        return FileResult(
            filename=src.name,
            detected_language="en",
            duration=3.0,
            segments=[Segment(start=0.0, end=3.0, text=f"content of {src.name}", language="en")],
        )


def _wait_done(manager: JobManager, job_id: str, timeout: float = 5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = manager.get(job_id)
        if job and job.status.state in (JobState.DONE, JobState.ERROR):
            return job
        time.sleep(0.05)
    raise AssertionError("job did not finish in time")


def test_full_job_flow_writes_combined_output(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs_module, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(jobs_module, "OUTPUT_DIR", tmp_path / "outputs")
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)

    src_a = tmp_path / "a.mp3"
    src_b = tmp_path / "b.wav"
    src_a.write_bytes(b"x")
    src_b.write_bytes(b"y")

    manager = JobManager(engine=StubEngine())
    opts = TranscribeOptions(output_format=OutputFormat.TXT)
    job = manager.create_job([src_a, src_b], opts)
    manager.start(job.job_id)

    finished = _wait_done(manager, job.job_id)
    assert finished.status.state == JobState.DONE
    assert finished.output_path is not None and finished.output_path.exists()

    text = finished.output_path.read_text(encoding="utf-8")
    assert "content of a.mp3" in text
    assert "content of b.wav" in text
    assert all(f.state == JobState.DONE for f in finished.status.files)


def test_per_file_error_is_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs_module, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(jobs_module, "OUTPUT_DIR", tmp_path / "outputs")
    (tmp_path / "outputs").mkdir(parents=True, exist_ok=True)

    class FlakyEngine(StubEngine):
        def transcribe_file(self, src, work_wav, options, on_progress=None):
            if src.name == "bad.mp3":
                raise RuntimeError("decode failed")
            return super().transcribe_file(src, work_wav, options, on_progress)

    good = tmp_path / "good.mp3"
    bad = tmp_path / "bad.mp3"
    good.write_bytes(b"x")
    bad.write_bytes(b"y")

    manager = JobManager(engine=FlakyEngine())
    job = manager.create_job([good, bad], TranscribeOptions(output_format=OutputFormat.TXT))
    manager.start(job.job_id)

    finished = _wait_done(manager, job.job_id)
    assert finished.status.state == JobState.DONE
    states = {f.filename: f.state for f in finished.status.files}
    assert states["good.mp3"] == JobState.DONE
    assert states["bad.mp3"] == JobState.ERROR


def test_prune_old_data_removes_stale_entries(tmp_path, monkeypatch):
    """Old job directories go, recent ones stay."""
    from app import housekeeping

    uploads = tmp_path / "uploads"
    outputs = tmp_path / "outputs"
    uploads.mkdir()
    outputs.mkdir()

    stale = uploads / "old-job"
    stale.mkdir()
    clip = stale / "clip.mp4"
    clip.write_bytes(b"x" * 2048)
    old_time = time.time() - 30 * 86400
    os.utime(clip, (old_time, old_time))
    os.utime(stale, (old_time, old_time))

    fresh = uploads / "new-job"
    fresh.mkdir()
    (fresh / "clip.mp4").write_bytes(b"y" * 512)

    monkeypatch.setattr(housekeeping, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(housekeeping, "OUTPUT_DIR", outputs)

    removed, freed = housekeeping.prune_old_data(retention_days=7)

    assert removed == 1
    assert freed == 2048
    assert not stale.exists()
    assert fresh.exists()


def test_prune_old_data_disabled_by_zero_retention(tmp_path, monkeypatch):
    """A retention of 0 keeps everything, however old."""
    from app import housekeeping

    uploads = tmp_path / "uploads"
    uploads.mkdir()
    stale = uploads / "ancient"
    stale.mkdir()
    old_time = time.time() - 365 * 86400
    os.utime(stale, (old_time, old_time))

    outputs = tmp_path / "outputs"
    outputs.mkdir()
    monkeypatch.setattr(housekeeping, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(housekeeping, "OUTPUT_DIR", outputs)

    assert housekeeping.prune_old_data(retention_days=0) == (0, 0)
    assert stale.exists()


def test_job_where_every_file_fails_reports_error(tmp_path, monkeypatch):
    """A green "done" with an empty transcript is the worst possible outcome.

    This is the first-run failure path: no network for the model download, or a
    missing ffmpeg, makes every file raise.
    """
    from app.models import JobState, OutputFormat, TranscribeOptions

    class AlwaysFails:
        def transcribe_file(self, *args, **kwargs):
            raise RuntimeError("ffmpeg is not installed")

    monkeypatch.setattr(jobs_module, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(jobs_module, "OUTPUT_DIR", tmp_path / "outputs")

    manager = JobManager(engine=AlwaysFails())
    src = tmp_path / "a.mp3"
    src.write_bytes(b"x")
    job = manager.create_job([src], TranscribeOptions(output_format=OutputFormat.TXT))
    manager.start(job.job_id)
    for _ in range(100):
        if job.status.state in (JobState.DONE, JobState.ERROR):
            break
        time.sleep(0.02)

    assert job.status.state == JobState.ERROR
    assert "ffmpeg" in (job.status.error or "")
    assert job.output_path is None


def test_discard_removes_a_job_that_never_started():
    from app.models import OutputFormat, TranscribeOptions

    manager = JobManager()
    job = manager.create_job([], TranscribeOptions(output_format=OutputFormat.TXT))
    assert manager.get(job.job_id) is not None
    manager.discard(job.job_id)
    assert manager.get(job.job_id) is None


def test_prune_keeps_a_directory_whose_contents_are_fresh(tmp_path, monkeypatch):
    """A long-running job writes into a subdirectory without touching the
    parent's mtime. Keying on the parent alone would delete its sources."""
    from app import housekeeping

    uploads = tmp_path / "uploads"
    outputs = tmp_path / "outputs"
    uploads.mkdir()
    outputs.mkdir()

    running = uploads / "long-job"
    (running / "wav").mkdir(parents=True)
    (running / "wav" / "part.wav").write_bytes(b"z" * 64)
    old_time = time.time() - 30 * 86400
    os.utime(running, (old_time, old_time))  # parent looks ancient

    monkeypatch.setattr(housekeeping, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(housekeeping, "OUTPUT_DIR", outputs)

    removed, _ = housekeeping.prune_old_data(retention_days=7)
    assert removed == 0
    assert running.exists()


def test_prune_skips_protected_jobs(tmp_path, monkeypatch):
    """Ids of jobs the manager still knows about are never swept."""
    from app import housekeeping

    uploads = tmp_path / "uploads"
    outputs = tmp_path / "outputs"
    uploads.mkdir()
    outputs.mkdir()

    old_time = time.time() - 30 * 86400
    for name in ("keep-me", "sweep-me"):
        job_dir = uploads / name
        job_dir.mkdir()
        f = job_dir / "clip.mp4"
        f.write_bytes(b"x" * 100)
        os.utime(f, (old_time, old_time))
        os.utime(job_dir, (old_time, old_time))

    monkeypatch.setattr(housekeeping, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(housekeeping, "OUTPUT_DIR", outputs)

    removed, _ = housekeeping.prune_old_data(retention_days=7, protected={"keep-me"})
    assert removed == 1
    assert (uploads / "keep-me").exists()
    assert not (uploads / "sweep-me").exists()
