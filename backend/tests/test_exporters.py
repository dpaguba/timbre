from __future__ import annotations

from app.exporters import export
from app.exporters._shared import format_timestamp
from app.models import OutputFormat, TranscribeOptions

from .factories import sample_results


def test_format_timestamp():
    assert format_timestamp(0) == "00:00:00"
    assert format_timestamp(65) == "00:01:05"
    assert format_timestamp(3661) == "01:01:01"


def test_txt_export_has_section_per_file(tmp_path):
    dst = tmp_path / "out.txt"
    opts = TranscribeOptions(output_format=OutputFormat.TXT)
    export(sample_results(), opts, dst)
    text = dst.read_text(encoding="utf-8")
    assert "interview_en.mp3" in text
    assert "mixed_de_uk.mp4" in text
    assert "Hello and welcome." in text
    assert "Доброго дня." in text


def test_markdown_export_has_headings_and_toc(tmp_path):
    dst = tmp_path / "out.md"
    opts = TranscribeOptions(output_format=OutputFormat.MARKDOWN)
    export(sample_results(), opts, dst)
    text = dst.read_text(encoding="utf-8")
    assert "# Transcript" in text
    assert "## 1. interview_en.mp3" in text
    assert "## 2. mixed_de_uk.mp4" in text
    assert "## Contents" in text


def test_markdown_without_timestamps(tmp_path):
    dst = tmp_path / "out.md"
    opts = TranscribeOptions(output_format=OutputFormat.MARKDOWN, include_timestamps=False)
    export(sample_results(), opts, dst)
    text = dst.read_text(encoding="utf-8")
    assert "`00:00:00`" not in text
    assert "Today we talk about testing." in text


def test_docx_export_creates_file(tmp_path):
    import pytest

    pytest.importorskip("docx")
    dst = tmp_path / "out.docx"
    opts = TranscribeOptions(output_format=OutputFormat.DOCX)
    export(sample_results(), opts, dst)
    assert dst.exists() and dst.stat().st_size > 0
