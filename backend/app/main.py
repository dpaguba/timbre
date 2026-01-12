"""FastAPI application entry point.

Serves the JSON API under ``/api`` and, when the frontend has been built, the
static SPA from the same origin so the whole tool runs from one process.

The server binds to localhost, so the middleware stack is what keeps "local
only" true. It is assembled differently for the two ways the app runs.

In the browser build there is no token. ``RejectForeignOriginMiddleware`` is
the guard: ``multipart/form-data`` is CORS-safelisted, so a POST from any page
runs without a preflight and CORS alone would only decide whether the response
is readable, not whether the request happened. ``TrustedHostMiddleware`` pins
the host to localhost, and CORS is not needed at all because the API serves the
page itself. That allowlist carries no ports: Starlette strips the port from the
host header before matching, so a port-suffixed entry would never fire.

In the desktop build the shell passes a random per-launch token that every API
call must carry, which is a guarantee no Origin header can make. The frontend
ships inside the app and runs on Tauri's own scheme, so those calls are
cross-origin by construction and CORS has to allow the Tauri origins; the token
is what authorises them. The port is chosen at random too, so the host
allowlist cannot apply and is opened up.
"""
from __future__ import annotations

import asyncio
import logging
import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .config import (
    AUTH_TOKEN,
    DEV_MODE,
    DEV_ORIGINS,
    FRONTEND_DIST,
    LOCAL_ORIGINS,
    MAX_JOB_BYTES,
    PRUNE_INTERVAL_SECONDS,
    ensure_dirs,
)
from .housekeeping import prune_old_data
from .routers import transcribe

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("timbre")


async def _housekeeping_loop() -> None:
    """Prune on a timer, not only at startup.

    A server left running for weeks would otherwise never prune, which is the
    case the retention setting exists for. Jobs the manager still knows about
    are protected so a sweep cannot delete the sources of a running job.
    """
    while True:
        await asyncio.sleep(PRUNE_INTERVAL_SECONDS)
        try:
            live = set(transcribe.manager.active_job_ids())
            removed, freed = await asyncio.to_thread(prune_old_data, None, live)
            if removed:
                log.info("removed %d old item(s), freed %.1f MB", removed, freed / 1024 / 1024)
        except Exception:
            log.exception("housekeeping sweep failed")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepare the data directory, then sweep it off the event loop.

    A large data directory would otherwise make startup look like a hang, with
    uvicorn not yet accepting connections.
    """
    ensure_dirs()
    removed, freed = await asyncio.to_thread(prune_old_data)
    if removed:
        log.info("removed %d old item(s), freed %.1f MB", removed, freed / 1024 / 1024)

    task = asyncio.create_task(_housekeeping_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    title="Timbre",
    version="0.1.0",
    description="Local audio/video transcription.",
    lifespan=lifespan,
)


class RequireTokenMiddleware(BaseHTTPMiddleware):
    """Desktop mode: every API call carries the token the shell was given.

    The page itself is served without it so the webview can load and read the
    token out of its own URL; from then on it travels in a header.
    """

    async def dispatch(self, request, call_next):
        path = request.url.path
        if not AUTH_TOKEN or not path.startswith("/api/"):
            return await call_next(request)

        header = request.headers.get("authorization", "")
        supplied = header[7:] if header.lower().startswith("bearer ") else request.query_params.get("token")
        if not supplied or not secrets.compare_digest(supplied, AUTH_TOKEN):
            return JSONResponse({"detail": "Not authorised."}, status_code=401)
        return await call_next(request)


class RejectForeignOriginMiddleware(BaseHTTPMiddleware):
    """Refuse requests that came from another site.

    Without this check, a page sitting in a background tab could create jobs on
    the local server. It applies to the browser build only: the desktop shell
    runs on its own scheme and is protected by the token instead.
    """

    async def dispatch(self, request, call_next):
        if AUTH_TOKEN:
            return await call_next(request)
        origin = request.headers.get("origin")
        if origin and origin not in _ALLOWED_ORIGINS:
            return JSONResponse(
                {"detail": "Cross-origin requests are not accepted by this local server."},
                status_code=403,
            )
        return await call_next(request)


class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    """Reject oversized bodies before anything is read.

    Starlette buffers the whole multipart body into a temporary file while
    parsing the form, so a check inside the endpoint happens after the upload
    has already landed on disk. This is the only place that can stop it.
    """

    async def dispatch(self, request, call_next):
        if request.method == "POST":
            declared = request.headers.get("content-length")
            if declared and declared.isdigit() and int(declared) > MAX_JOB_BYTES:
                return JSONResponse(
                    {
                        "detail": (
                            f"Upload is larger than the {MAX_JOB_BYTES // 1024 ** 3} GB limit. "
                            "Upload fewer files at once, or raise TIMBRE_MAX_JOB_BYTES."
                        )
                    },
                    status_code=413,
                )
        return await call_next(request)


_ALLOWED_HOSTS = ["*"] if AUTH_TOKEN else ["localhost", "127.0.0.1", "testserver"]

_ALLOWED_ORIGINS = set(LOCAL_ORIGINS) | (set(DEV_ORIGINS) if DEV_MODE else set())

_CORS_ORIGINS: list[str] = []
if AUTH_TOKEN:
    _CORS_ORIGINS = ["tauri://localhost", "http://tauri.localhost", "https://tauri.localhost"]
if DEV_MODE:
    _CORS_ORIGINS += DEV_ORIGINS

app.add_middleware(LimitUploadSizeMiddleware)
app.add_middleware(RequireTokenMiddleware)
app.add_middleware(RejectForeignOriginMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_ALLOWED_HOSTS)

if _CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(transcribe.router)


if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(FRONTEND_DIST / "index.html")

    @app.get("/{full_path:path}")
    def spa_fallback(full_path: str) -> FileResponse:
        """Answer unknown paths with the SPA shell, with two exceptions.

        An unknown ``/api`` path is a real 404 and must not receive HTML. Files
        Vite copies from ``public/`` land at the root of ``dist`` rather than
        under ``/assets``, so favicon.png and friends have to be served as
        themselves or they render as a broken image.
        """
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")

        candidate = (FRONTEND_DIST / full_path).resolve()
        if (
            full_path
            and candidate.is_file()
            and candidate.is_relative_to(FRONTEND_DIST.resolve())
        ):
            return FileResponse(candidate)

        return FileResponse(FRONTEND_DIST / "index.html")
