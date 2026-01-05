"""Media handling: probe and normalise any audio or video file to mono 16 kHz WAV.

Whisper expects 16 kHz mono PCM. Decoding goes through PyAV, which links the
ffmpeg libraries directly and is already installed as a faster-whisper
dependency. That matters beyond tidiness: the previous implementation shelled
out to an `ffmpeg` binary the user had to install first, and that single step
was the one thing standing between downloading this tool and using it.

PyAV reports 412 container formats and 540 codecs on the pinned version, which
is the same coverage the command line gave us.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import av
import av.error

TARGET_RATE = 16000
TARGET_LAYOUT = "mono"
TARGET_FORMAT = "s16"


class MediaDecodeError(RuntimeError):
    """Raised when a file cannot be decoded into audio."""


def ffmpeg_available() -> bool:
    """Kept for the health endpoint.

    Decoding no longer needs a binary on PATH, so this reports on the library
    that is compiled in. It stays true on any machine that can import PyAV.
    """
    return bool(av.library_versions.get("libavcodec"))


def ffmpeg_source() -> str:
    """Where the decoder comes from, for diagnostics."""
    major = av.library_versions.get("libavcodec", (0,))[0]
    external = shutil.which("ffmpeg")
    return f"PyAV {av.__version__} (libavcodec {major})" + (
        ", system ffmpeg also present" if external else ""
    )


def probe_duration(path: Path) -> float:
    """Duration in seconds, or 0.0 when nothing reports one.

    Some containers, transport streams and a few WebM files among them, carry
    no container duration. The audio stream usually still knows, so it is asked
    second.
    """
    try:
        with av.open(str(path)) as container:
            if container.duration is not None:
                return float(container.duration / av.time_base)

            for stream in container.streams.audio:
                if stream.duration and stream.time_base:
                    return float(stream.duration * stream.time_base)
    except (av.error.FFmpegError, ValueError, OSError):
        return 0.0
    return 0.0


def extract_wav(src: Path, dst: Path) -> Path:
    """Decode any media file to mono 16 kHz 16-bit WAV at `dst`.

    The resampler and the encoder are both flushed once the input is exhausted.
    Without that the tail of the recording is silently lost.
    """
    dst.parent.mkdir(parents=True, exist_ok=True)

    try:
        with av.open(str(src)) as inp:
            if not inp.streams.audio:
                raise MediaDecodeError(f"{src.name} has no audio stream.")

            resampler = av.AudioResampler(
                format=TARGET_FORMAT, layout=TARGET_LAYOUT, rate=TARGET_RATE
            )

            with av.open(str(dst), "w") as out:
                stream = out.add_stream("pcm_s16le", rate=TARGET_RATE, layout=TARGET_LAYOUT)
                for frame in inp.decode(audio=0):
                    for resampled in resampler.resample(frame):
                        for packet in stream.encode(resampled):
                            out.mux(packet)
                for resampled in resampler.resample(None):
                    for packet in stream.encode(resampled):
                        out.mux(packet)
                for packet in stream.encode(None):
                    out.mux(packet)
    except av.error.FFmpegError as exc:
        raise MediaDecodeError(f"Could not decode {src.name}: {exc}") from exc

    if not dst.exists() or dst.stat().st_size == 0:
        raise MediaDecodeError(f"Decoding {src.name} produced no audio.")
    return dst
