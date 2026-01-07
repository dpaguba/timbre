"""Exporters turn a list of FileResult into a single combined document."""
from __future__ import annotations

from pathlib import Path

from ..models import FileResult, OutputFormat, TranscribeOptions
from .docx_exporter import export_docx
from .markdown_exporter import export_markdown
from .txt_exporter import export_txt

_EXPORTERS = {
    OutputFormat.TXT: export_txt,
    OutputFormat.MARKDOWN: export_markdown,
    OutputFormat.DOCX: export_docx,
}


def export(results: list[FileResult], options: TranscribeOptions, dst: Path) -> Path:
    """Write the combined transcript to `dst` in the requested format."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    exporter = _EXPORTERS[options.output_format]
    return exporter(results, options, dst)


__all__ = ["export", "export_docx", "export_markdown", "export_txt"]
