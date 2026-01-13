"""Small helpers to build test fixtures."""
from __future__ import annotations

from app.models import FileResult, Segment


def sample_results() -> list[FileResult]:
    return [
        FileResult(
            filename="interview_en.mp3",
            detected_language="en",
            duration=12.0,
            segments=[
                Segment(start=0.0, end=4.0, text="Hello and welcome.", language="en"),
                Segment(start=4.0, end=12.0, text="Today we talk about testing.", language="en"),
            ],
        ),
        FileResult(
            filename="mixed_de_uk.mp4",
            detected_language="de",
            duration=8.0,
            segments=[
                Segment(start=0.0, end=4.0, text="Guten Tag.", language="de"),
                Segment(start=4.0, end=8.0, text="Доброго дня.", language="uk"),
            ],
        ),
    ]
