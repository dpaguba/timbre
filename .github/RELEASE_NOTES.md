Transcribe audio and video into one document, entirely on your own machine.

## Downloads

| Platform | File |
|---|---|
| macOS, Apple Silicon | `Timbre_*_aarch64.dmg` |
| macOS, Intel | `Timbre_*_x64.dmg` |
| Windows | `Timbre_*_x64-setup.exe` |

## First run

These builds are not signed with a paid certificate yet, so both systems ask
before opening an app they cannot attribute.

**macOS.** Open the DMG and drag the app to Applications, then open it once.
macOS says it cannot verify the app and offers only Move to Trash: choose
**Done**. Now open System Settings, go to Privacy & Security, scroll to the
bottom, and press **Open Anyway** next to the message about Timbre. It asks for
your password and the app starts. From then on it opens normally.

Control-clicking the app and choosing Open used to work and no longer does;
macOS Sequoia removed that shortcut. One command does the same job:

```bash
xattr -dr com.apple.quarantine /Applications/Timbre.app
```

**Windows.** SmartScreen shows "Windows protected your PC". Choose More info,
then Run anyway.

## What happens on first launch

The app downloads one transcription model, about 480 MB for the recommended
one. That is the only time it uses the network. After it finishes, everything
works offline, and your recordings never leave the computer.

## Requirements

None. Python, ffmpeg and the transcription engine are inside the download.
