## What this changes

<!-- One or two sentences. Link the issue if there is one. -->

## Why

<!-- What was wrong, or what became possible. -->

## Checklist

- [ ] `cd backend && pytest` passes
- [ ] `cd backend && ruff check app tests` is clean
- [ ] `cd frontend && npm run lint && npm run typecheck && npm run build` is clean
- [ ] `cd desktop/src-tauri && cargo fmt --check && cargo clippy -- -D warnings` is clean, if the shell changed
- [ ] A test covers the change, if it is a bug fix or a new format
