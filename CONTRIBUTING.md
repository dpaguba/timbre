# Contributing to Timbre

Thanks for your interest in improving Timbre. Issues and pull requests are
both welcome; participation is covered by the [Code of Conduct](./CODE_OF_CONDUCT.md).

Security problems do not belong in a public issue. Use the Security tab, see
[SECURITY.md](./SECURITY.md).

## Getting set up

You need Python 3.10+ and Node 18+. You do not need ffmpeg: decoding goes
through PyAV, which links the ffmpeg libraries itself and arrives with the
Python dependencies.

```bash
./dev.sh          # macOS and Linux
```

```powershell
.\dev.ps1         # Windows
```

That starts the backend with reload on `:8000` and the Vite dev server on
`:5173`, and creates the virtual environment on first run.

To work on the desktop shell you also need a Rust toolchain. The shell loads
the server from its own resources, so build that first:

```bash
cd frontend && npm run build
cd ../backend && pip install pyinstaller && pyinstaller timbre-server.spec --noconfirm
cd ..
rm -rf desktop/src-tauri/server && cp -R backend/dist/timbre-server desktop/src-tauri/server
rm -rf desktop/src-tauri/licenses && cp -R licenses desktop/src-tauri/licenses
cd desktop && npm install && npx tauri build
```

Both staged directories are build inputs and are git-ignored. The licences have
to be there because GPL and LGPL each require their text to accompany the
binary.

## Project layout

```
backend/            FastAPI app
  app/
    main.py         Entry point: middleware, API, and the built SPA
    config.py       Settings, all environment-overridable
    models.py       Pydantic schemas
    media.py        PyAV probe and WAV extraction
    transcription.py faster-whisper engine wrapper
    jobs.py         In-memory job manager and background worker
    models_store.py What is downloaded, and how to download more
    housekeeping.py Retention sweep over uploads and outputs
    batch.py        Folder-at-a-time command line mode
    exporters/      TXT, Markdown and DOCX writers
    routers/        HTTP endpoints
  server.py         Entry point for the packaged build
  tests/            Pytest suite
frontend/           React, Vite, TypeScript and Tailwind
  src/
    App.tsx         Top-level state and polling
    api.ts          Typed API client
    desktop.ts      Everything that only exists inside the desktop build
    components/     Shell, dropzones, language picker, settings, models page
desktop/            Tauri shell
  src-tauri/src/    Sidecar startup, window, native menu
```

## Conventions

- **Comments are documentation.** Docstrings, JSDoc and Rust doc comments
  explain what something is for. Running commentary inside a function body does
  not: if a line needs explaining, the explanation belongs in the docstring.
- **Backend:** keep modules small and single-purpose. Heavy dependencies
  (`faster_whisper`, `docx`) are imported lazily so tests and startup do not pay
  for them.
- **Frontend:** every colour, size and spacing value comes from
  [DESIGN.md](./DESIGN.md); reach for a token before inventing a value.
  TypeScript strict mode, and the interface works from the keyboard. The custom select implements the ARIA listbox pattern; anything
  replacing a native control has to keep what the native one gave away for free.
- Prefer adding a test alongside any bug fix or new exporter.

Before opening a pull request:

```bash
(cd backend && pytest && ruff check app tests)
(cd frontend && npm run lint && npm run typecheck && npm run build)
(cd desktop/src-tauri && cargo fmt --check && cargo clippy -- -D warnings)
```

Each line runs in a subshell, so all three start from the repository root.
Clippy compiles the SPA that gets embedded in the shell, which is why the
frontend build comes before it. CI runs the same three on every pull request.
Ruff's configuration is in `backend/ruff.toml`.

## Adding an output format

1. Create `backend/app/exporters/<name>_exporter.py` exposing
   `export_<name>(results, options, dst) -> Path`.
2. Register it in `exporters/__init__.py` and add the enum value in
   `models.py` (`OutputFormat`).
3. Add the option to `frontend/src/components/Settings.tsx`.
4. Add a test in `backend/tests/`.

## Adding a dependency

Check its licence first and add it to [NOTICE.md](./NOTICE.md). The project is
MIT and the released binaries already carry a GPL obligation through FFmpeg;
that list is how anyone redistributing a build knows what they are handling.

## Pull requests

Keep them focused and say what changed and why. A screenshot helps for anything
visible.
