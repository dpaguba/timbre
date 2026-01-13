"""Decoding through PyAV.

These build real media with PyAV and decode it back, rather than mocking: the
whole point of the module is that it talks to a real codec correctly, and a
mock would pass whatever we told it to.
"""
from __future__ import annotations

import wave

import av
import pytest

from app.media import MediaDecodeError, extract_wav, ffmpeg_available, probe_duration


def make_media(path, seconds=1.0, rate=44100, layout="stereo", codec="pcm_s16le"):
    """Write a short tone so there is something real to decode."""
    import math

    with av.open(str(path), "w") as container:
        stream = container.add_stream(codec, rate=rate, layout=layout)
        channels = 2 if layout == "stereo" else 1
        samples = int(rate * seconds)
        frame_size = 1024
        written = 0
        while written < samples:
            count = min(frame_size, samples - written)
            frame = av.AudioFrame(format="s16", layout=layout, samples=count)
            frame.sample_rate = rate
            frame.pts = written
            buf = bytearray()
            for i in range(count):
                value = int(8000 * math.sin(2 * math.pi * 440 * (written + i) / rate))
                buf += int(value).to_bytes(2, "little", signed=True) * channels
            frame.planes[0].update(bytes(buf))
            for packet in stream.encode(frame):
                container.mux(packet)
            written += count
        for packet in stream.encode(None):
            container.mux(packet)
    return path


def test_decoder_is_available():
    """The bundled libraries, not a binary on PATH."""
    assert ffmpeg_available() is True


def test_extract_wav_produces_16k_mono(tmp_path):
    src = make_media(tmp_path / "tone.wav", seconds=1.0, rate=44100, layout="stereo")
    dst = extract_wav(src, tmp_path / "out" / "tone16.wav")

    assert dst.exists()
    with wave.open(str(dst)) as w:
        assert w.getframerate() == 16000
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        assert 15000 <= w.getnframes() <= 17000


def test_extract_wav_creates_the_destination_directory(tmp_path):
    src = make_media(tmp_path / "a.wav", seconds=0.2)
    dst = extract_wav(src, tmp_path / "deep" / "nested" / "a16.wav")
    assert dst.is_file()


def test_probe_duration_reads_the_container(tmp_path):
    src = make_media(tmp_path / "two.wav", seconds=2.0)
    assert 1.8 <= probe_duration(src) <= 2.2


def test_probe_duration_is_zero_for_a_non_media_file(tmp_path):
    junk = tmp_path / "notes.txt"
    junk.write_text("this is not audio")
    assert probe_duration(junk) == 0.0


def test_decoding_a_non_media_file_raises(tmp_path):
    junk = tmp_path / "notes.txt"
    junk.write_text("this is not audio")
    with pytest.raises(MediaDecodeError):
        extract_wav(junk, tmp_path / "out.wav")


def test_decoding_a_video_without_audio_raises(tmp_path):
    path = tmp_path / "silent.mp4"
    with av.open(str(path), "w") as container:
        stream = container.add_stream("mpeg4", rate=5)
        stream.width, stream.height, stream.pix_fmt = 64, 64, "yuv420p"
        for i in range(5):
            frame = av.VideoFrame(64, 64, "yuv420p")
            frame.pts = i
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode(None):
            container.mux(packet)

    with pytest.raises(MediaDecodeError, match="no audio"):
        extract_wav(path, tmp_path / "out.wav")
