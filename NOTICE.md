# Third-party notices

Timbre's own source is [MIT licensed](./LICENSE). It stands on other
people's work, listed here with the licence each is distributed under.

## Please read this before redistributing a build

**The released desktop binaries are not MIT.** They are a combined work that
includes GPL-2.0-or-later code, and are therefore distributed under
GPL-2.0-or-later. This project's source stays MIT, and the full source of the
combined work is this repository.

The reason is FFmpeg. Decoding goes through [PyAV](https://github.com/PyAV-Org/PyAV),
whose published wheels bundle FFmpeg shared libraries built with **libx264** and
**libx265**, both GPL-2.0-or-later. Timbre never encodes video and never
calls either of them, but `libavcodec`, `libavformat`, `libavfilter` and
`libavdevice` all record a hard link to them and refuse to load when they are
absent, so they cannot simply be dropped from the bundle. Removing this
constraint means building PyAV against an FFmpeg configured without those
encoders.

Running from source is unaffected. Installing the same wheels for your own use
is not redistribution.

Both licence texts travel inside every build, in `licenses/` beside the app's
own resources, and the app opens that folder from **Help → Licences**.

## Transcription

| Component | Licence |
|---|---|
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | MIT |
| [CTranslate2](https://github.com/OpenNMT/CTranslate2) | MIT |
| [Whisper](https://github.com/openai/whisper) models, in their CTranslate2 conversions | MIT |
| [tokenizers](https://github.com/huggingface/tokenizers) | Apache-2.0 |
| [huggingface_hub](https://github.com/huggingface/huggingface_hub) | Apache-2.0 |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | MIT |

Models are downloaded on first run and cached; none of them ships in the
repository or in a release.

## Media decoding

| Component | Licence |
|---|---|
| [PyAV](https://github.com/PyAV-Org/PyAV) | BSD-3-Clause |
| [FFmpeg](https://ffmpeg.org) libraries bundled by PyAV | LGPL-2.1-or-later, and GPL-2.0-or-later as built |
| [x264](https://www.videolan.org/developers/x264.html), [x265](https://www.videolan.org/developers/x265.html) | GPL-2.0-or-later |

## Backend

| Component | Licence |
|---|---|
| [FastAPI](https://github.com/fastapi/fastapi) | MIT |
| [Starlette](https://github.com/encode/starlette) | BSD-3-Clause |
| [Uvicorn](https://github.com/encode/uvicorn) | BSD-3-Clause |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT |
| [python-multipart](https://github.com/Kludex/python-multipart) | Apache-2.0 |
| [python-docx](https://github.com/python-openxml/python-docx) | MIT |
| [CPython](https://github.com/python/cpython), bundled whole by PyInstaller | PSF-2.0 |
| The [PyInstaller](https://github.com/pyinstaller/pyinstaller) bootloader, linked into the packaged server | GPL-2.0 with the bootloader exception, which is what permits distributing it inside a non-GPL application |

## Desktop shell and interface

| Component | Licence |
|---|---|
| [Tauri](https://github.com/tauri-apps/tauri) | MIT or Apache-2.0 |
| [React](https://github.com/facebook/react) | MIT |
| [Vite](https://github.com/vitejs/vite) | MIT |
| [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) | MIT |
| [Inter](https://github.com/rsms/inter) | SIL OFL 1.1, see [licenses/Inter-OFL.txt](./licenses/Inter-OFL.txt) |
| [EB Garamond](https://github.com/octaviopardo/EBGaramond12) | SIL OFL 1.1, see [licenses/EBGaramond-OFL.txt](./licenses/EBGaramond-OFL.txt) |

Both fonts are served from the application itself rather than from a font CDN,
so the interface loads with the network off and no request leaves the machine.
