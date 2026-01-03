"""Pydantic schemas shared across the API and the transcription engine."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class OutputFormat(str, Enum):
    TXT = "txt"
    MARKDOWN = "md"
    DOCX = "docx"


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class TranscribeOptions(BaseModel):
    """User-selected transcription settings for a job."""

    languages: list[str] = Field(
        default_factory=list,
        description=(
            "ISO 639-1 codes the user expects in the media, for example "
            '["en", "de", "uk"]. An empty list auto-detects.'
        ),
    )
    multilingual: bool = Field(
        default=False,
        description=(
            "Detect the language per segment rather than per file, so a "
            "recording that mixes languages is handled correctly."
        ),
    )
    model: str = "small"
    output_format: OutputFormat = OutputFormat.MARKDOWN
    include_timestamps: bool = Field(
        default=True, description="Include timestamps in the exported document."
    )


class Segment(BaseModel):
    start: float
    end: float
    text: str
    language: str | None = None


class FileResult(BaseModel):
    """Transcription result for a single source file."""

    filename: str
    detected_language: str | None = None
    duration: float = 0.0
    segments: list[Segment] = Field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments).strip()


class FileProgress(BaseModel):
    filename: str
    state: JobState = JobState.QUEUED
    progress: float = 0.0  # 0..1
    detected_language: str | None = None
    error: str | None = None


class JobStatus(BaseModel):
    job_id: str
    state: JobState
    options: TranscribeOptions
    files: list[FileProgress] = Field(default_factory=list)
    error: str | None = None

    @property
    def progress(self) -> float:
        if not self.files:
            return 0.0
        return sum(f.progress for f in self.files) / len(self.files)
