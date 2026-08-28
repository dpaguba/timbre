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

**macOS.** Open the DMG, drag the app to Applications, then right-click it and
choose Open. Confirm once. Double-clicking without that first step shows a
message saying the app cannot be checked, which is the same block, worded
unhelpfully.

If macOS refuses outright, clear the quarantine flag:

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
