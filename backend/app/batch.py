"""Batch transcription: transcribe every media file in a folder, one by one,
into a single combined document.

Designed for large jobs (dozens of big files, many hours on CPU):

  * Files are processed in natural order (1.mp4, 2.mp4, ..., 10.mp4).
  * Progress is saved after every file, so the combined document is always
    up to date and a crash never loses completed work.
  * Re-running the same command resumes: already-transcribed files are skipped.

Usage (from the `backend` directory, using the project venv):

    python -m app.batch --input /path/to/folder \
        --languages ru,uk,en --model small --format md

Run `python -m app.batch --help` for all options.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path

from .exporters import export
from .media import ffmpeg_available
from .models import FileResult, Segment, TranscribeOptions
from .transcription import WhisperEngine

MEDIA_EXTS = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".flv", ".wmv", ".mpeg", ".mpg",
    ".mp3", ".wav", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".flac", ".wma",
}


def natural_key(path: Path):
    """Sort so that '2.mp4' comes before '10.mp4'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", path.name)]


def find_media(folder: Path) -> list[Path]:
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in MEDIA_EXTS]
    return sorted(files, key=natural_key)



def _result_to_dict(r: FileResult) -> dict:
    return {
        "filename": r.filename,
        "detected_language": r.detected_language,
        "duration": r.duration,
        "segments": [
            {"start": s.start, "end": s.end, "text": s.text, "language": s.language}
            for s in r.segments
        ],
    }


def _result_from_dict(d: dict) -> FileResult:
    return FileResult(
        filename=d["filename"],
        detected_language=d.get("detected_language"),
        duration=d.get("duration", 0.0),
        segments=[Segment(**s) for s in d.get("segments", [])],
    )


def load_progress(progress_path: Path) -> list[FileResult]:
    if not progress_path.exists():
        return []
    try:
        data = json.loads(progress_path.read_text(encoding="utf-8"))
        return [_result_from_dict(d) for d in data]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []


def save_progress(progress_path: Path, results: list[FileResult]) -> None:
    progress_path.write_text(
        json.dumps([_result_to_dict(r) for r in results], ensure_ascii=False, indent=1),
        encoding="utf-8",
    )



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Batch transcribe a folder of audio/video into one document.")
    p.add_argument("--input", "-i", type=Path, default=None,
                   help="Folder with media files (all media inside are transcribed).")
    p.add_argument("--files", nargs="+", type=Path, default=None,
                   help="Explicit media files to transcribe (alternative to --input).")
    p.add_argument("--output", "-o", type=Path, default=None,
                   help="Output file. Default: <input>/transcript.<format>")
    p.add_argument("--model", "-m", default="small", help="Whisper model (tiny/base/small/medium/large-v3).")
    p.add_argument("--languages", "-l", default="",
                   help="Comma-separated ISO codes, e.g. 'ru,uk,en'. Empty = auto-detect.")
    p.add_argument("--format", "-f", dest="fmt", default="md", choices=["txt", "md", "docx"],
                   help="Output format.")
    p.add_argument("--no-timestamps", action="store_true", help="Omit timestamps in the output.")
    p.add_argument("--limit", "-n", type=int, default=0,
                   help="Only process the first N files (0 = all). Useful for a quick test.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if not ffmpeg_available():
        print(
        "ERROR: PyAV could not load its bundled ffmpeg libraries. Reinstall the "
        "dependencies with 'pip install -r backend/requirements.txt'.",
        file=sys.stderr,
    )
        return 2

    if args.files:
        sources = []
        for f in args.files:
            if not f.is_file():
                print(f"ERROR: not a file: {f}", file=sys.stderr)
                return 2
            sources.append(f)
        sources = sorted(sources, key=natural_key)
        base_dir = sources[0].parent
        label = f"{len(sources)} explicit file(s)"
    elif args.input:
        if not args.input.is_dir():
            print(f"ERROR: not a folder: {args.input}", file=sys.stderr)
            return 2
        sources = find_media(args.input)
        if not sources:
            print(f"No media files found in {args.input}", file=sys.stderr)
            return 1
        base_dir = args.input
        label = args.input.name
    else:
        print("ERROR: provide --input FOLDER or --files FILE [FILE ...]", file=sys.stderr)
        return 2

    if args.limit and args.limit > 0:
        sources = sources[: args.limit]

    languages = [c.strip() for c in args.languages.split(",") if c.strip()]
    options = TranscribeOptions(
        languages=languages,
        multilingual=len(languages) > 1,
        model=args.model,
        include_timestamps=not args.no_timestamps,
    )
    from .models import OutputFormat
    options.output_format = OutputFormat(args.fmt)

    out_path: Path = args.output or (base_dir / f"transcript.{args.fmt}")
    progress_path = out_path.with_name(out_path.name + ".progress.json")

    done = load_progress(progress_path)
    done_names = {r.filename for r in done}
    results: list[FileResult] = list(done)

    total = len(sources)
    remaining = [s for s in sources if s.name not in done_names]
    print(f"Found {total} media files ({label}).")
    if done:
        print(f"Resuming: {len(done)} already done, {len(remaining)} to go.")
    lang_desc = ", ".join(languages) if languages else "auto-detect"
    print(f"Model: {args.model} | Languages: {lang_desc} | Output: {out_path}\n")

    engine = WhisperEngine()

    with tempfile.TemporaryDirectory(prefix="timbre-batch-") as tmp:
        work_dir = Path(tmp)
        for index, src in enumerate(sources, start=1):
            if src.name in done_names:
                print(f"[{index}/{total}] {src.name}  (already done, skipped)")
                continue

            print(f"[{index}/{total}] {src.name}  ...", flush=True)
            started = time.time()

            def on_progress(p: float, name=src.name) -> None:
                bar = int(p * 30)
                sys.stdout.write(f"\r    [{'#' * bar}{'.' * (30 - bar)}] {p * 100:5.1f}%")
                sys.stdout.flush()

            try:
                result = engine.transcribe_file(
                    src, work_dir / f"{index:03d}.wav", options, on_progress=on_progress
                )
                results.append(result)
                done_names.add(src.name)
                save_progress(progress_path, results)
                export(results, options, out_path)
                elapsed = time.time() - started
                print(
                    f"\r    done in {elapsed:5.0f}s  "
                    f"(lang: {result.detected_language}, {len(result.segments)} segments)"
                )
            except KeyboardInterrupt:
                print("\nInterrupted. Progress saved; re-run the same command to resume.")
                return 130
            except Exception as exc:  # noqa: BLE001
                print(f"\r    FAILED: {exc}")

    print(f"\nDone. Combined transcript written to:\n  {out_path}")
    print(f"(progress cache: {progress_path} — delete it to start fresh)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
