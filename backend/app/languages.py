"""Languages Whisper supports, exposed to the frontend for the picker.

A curated subset of the most common languages is listed first; the full set is
still accepted by the engine via ISO 639-1 codes.
"""
from __future__ import annotations

LANGUAGES: list[dict[str, str]] = [
    {"code": "en", "name": "English", "native": "English"},
    {"code": "de", "name": "German", "native": "Deutsch"},
    {"code": "uk", "name": "Ukrainian", "native": "Українська"},
    {"code": "ru", "name": "Russian", "native": "Русский"},
    {"code": "es", "name": "Spanish", "native": "Español"},
    {"code": "fr", "name": "French", "native": "Français"},
    {"code": "it", "name": "Italian", "native": "Italiano"},
    {"code": "pt", "name": "Portuguese", "native": "Português"},
    {"code": "pl", "name": "Polish", "native": "Polski"},
    {"code": "nl", "name": "Dutch", "native": "Nederlands"},
    {"code": "tr", "name": "Turkish", "native": "Türkçe"},
    {"code": "ar", "name": "Arabic", "native": "العربية"},
    {"code": "zh", "name": "Chinese", "native": "中文"},
    {"code": "ja", "name": "Japanese", "native": "日本語"},
    {"code": "ko", "name": "Korean", "native": "한국어"},
    {"code": "hi", "name": "Hindi", "native": "हिन्दी"},
    {"code": "cs", "name": "Czech", "native": "Čeština"},
    {"code": "sv", "name": "Swedish", "native": "Svenska"},
    {"code": "ro", "name": "Romanian", "native": "Română"},
    {"code": "el", "name": "Greek", "native": "Ελληνικά"},
]

MODELS = ["tiny", "base", "small", "medium", "large-v3"]
