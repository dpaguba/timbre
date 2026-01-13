from __future__ import annotations

from app.models import TranscribeOptions
from app.transcription import WhisperEngine


def test_single_language_is_forced():
    opts = TranscribeOptions(languages=["de"])
    lang, multilingual = WhisperEngine._resolve_language_mode(opts)
    assert lang == "de"
    assert multilingual is False


def test_multiple_languages_enable_multilingual_autodetect():
    opts = TranscribeOptions(languages=["de", "uk"])
    lang, multilingual = WhisperEngine._resolve_language_mode(opts)
    assert lang is None
    assert multilingual is True


def test_no_language_is_plain_autodetect():
    opts = TranscribeOptions(languages=[])
    lang, multilingual = WhisperEngine._resolve_language_mode(opts)
    assert lang is None
    assert multilingual is False


def test_multilingual_flag_forces_detection_even_with_one_language():
    opts = TranscribeOptions(languages=[], multilingual=True)
    lang, multilingual = WhisperEngine._resolve_language_mode(opts)
    assert lang is None
    assert multilingual is True
