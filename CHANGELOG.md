# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet.

## [0.1.0]

First public release.

### Added

- Transcribe any number of audio or video files into one document, entirely on
  your own machine, with faster-whisper.
- Desktop application for macOS and Windows. It carries its own Python, decoder
  and transcription engine, so there is nothing to install first.
- Onboarding on first launch: what the app is, which model to choose, and the
  one download it needs.
- Models page explaining what each model is for, with download and removal.
- Native integration: system open and save panels, drag from Finder or
  Explorer, a menu with the shortcuts you would try, progress on the dock or
  taskbar icon, and a notification when a long job finishes.
- Local files are transcribed in place. The desktop build passes a path rather
  than uploading, so a four gigabyte recording starts immediately.
- Output as plain text, Markdown or Word, with optional timestamps.
- Language selection: force one, name several for a recording that mixes them,
  or leave it to auto-detection.
- Batch mode for a whole folder, with progress saved after each file and resume
  after an interruption.
- Web mode: the same app served on `localhost` from a source checkout.
- Retention sweep that deletes old uploads and transcripts on a schedule, so the
  data directory does not grow until the disk is full.

### Security

- The desktop build authorises every API call with a token generated from the
  OS random source at each launch, on a randomly chosen port.
- The browser build refuses state-changing requests from other origins, which
  CORS alone would not prevent for multipart uploads, and pins the host header
  to localhost.
- Uploads are bounded per file and per job. The per-job total is refused from
  the declared content length, before the body is read; the per-file guard stops
  the copy as it runs.

[Unreleased]: https://github.com/dpaguba/timbre/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dpaguba/timbre/releases/tag/v0.1.0
