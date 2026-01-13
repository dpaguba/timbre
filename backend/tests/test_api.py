from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import FRONTEND_DIST
from app.main import app

client = TestClient(app)

needs_built_frontend = pytest.mark.skipif(
    not (FRONTEND_DIST / "assets").is_dir(),
    reason="the SPA routes are only mounted when the frontend has been built",
)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_languages_endpoint_lists_codes_and_models():
    res = client.get("/api/languages")
    assert res.status_code == 200
    body = res.json()
    codes = {lang["code"] for lang in body["languages"]}
    assert {"en", "de", "uk"}.issubset(codes)
    assert "small" in body["models"]


def test_create_job_rejects_bad_options():
    res = client.post(
        "/api/jobs",
        files=[("files", ("a.mp3", b"data", "audio/mpeg"))],
        data={"options": "not-json"},
    )
    assert res.status_code == 400


def test_job_not_found():
    res = client.get("/api/jobs/does-not-exist")
    assert res.status_code == 404


def test_upload_larger_than_per_file_limit_is_rejected(monkeypatch, tmp_path):
    """A file over the guard returns 413 and leaves nothing behind on disk."""
    import json as json_mod

    from app.routers import transcribe as router_mod

    uploads = tmp_path / "uploads"
    monkeypatch.setattr(router_mod, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(router_mod, "MAX_UPLOAD_BYTES", 1024)
    monkeypatch.setattr(router_mod, "MAX_JOB_BYTES", 10 * 1024)

    res = client.post(
        "/api/jobs",
        files=[("files", ("big.mp3", b"x" * 4096, "audio/mpeg"))],
        data={"options": json_mod.dumps({"languages": [], "model": "tiny", "output_format": "txt"})},
    )

    assert res.status_code == 413
    assert "per-file limit" in res.json()["detail"]
    assert not any(uploads.glob("*")) if uploads.exists() else True


def test_batch_larger_than_job_limit_is_rejected(monkeypatch, tmp_path):
    """Two files that each fit but together do not are rejected as a batch."""
    import json as json_mod

    from app.routers import transcribe as router_mod

    uploads = tmp_path / "uploads"
    monkeypatch.setattr(router_mod, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(router_mod, "MAX_UPLOAD_BYTES", 4096)
    monkeypatch.setattr(router_mod, "MAX_JOB_BYTES", 5000)

    res = client.post(
        "/api/jobs",
        files=[
            ("files", ("a.mp3", b"x" * 3000, "audio/mpeg")),
            ("files", ("b.mp3", b"y" * 3000, "audio/mpeg")),
        ],
        data={"options": json_mod.dumps({"languages": [], "model": "tiny", "output_format": "txt"})},
    )

    assert res.status_code == 413
    assert "total limit" in res.json()["detail"]


def test_accepted_upload_is_stored_byte_for_byte(monkeypatch, tmp_path):
    """The happy path through _copy_bounded, across more than one chunk."""
    import json as json_mod

    from app.routers import transcribe as router_mod

    uploads = tmp_path / "uploads"
    monkeypatch.setattr(router_mod, "UPLOAD_DIR", uploads)
    monkeypatch.setattr(router_mod, "MAX_UPLOAD_BYTES", 8 * 1024 * 1024)
    monkeypatch.setattr(router_mod, "MAX_JOB_BYTES", 8 * 1024 * 1024)
    monkeypatch.setattr(router_mod.manager, "start", lambda job_id: None)

    payload = bytes(range(256)) * 12_000  # ~3 MB, several 1 MB chunks
    res = client.post(
        "/api/jobs",
        files=[("files", ("clip.mp3", payload, "audio/mpeg"))],
        data={"options": json_mod.dumps({"languages": [], "model": "tiny", "output_format": "txt"})},
    )

    assert res.status_code == 200
    stored = list(uploads.rglob("clip.mp3"))
    assert len(stored) == 1
    assert stored[0].read_bytes() == payload


def test_unknown_model_is_rejected():
    """A model string with a slash would be fetched from Hugging Face."""
    import json as json_mod

    res = client.post(
        "/api/jobs",
        files=[("files", ("a.mp3", b"x", "audio/mpeg"))],
        data={"options": json_mod.dumps({"languages": [], "model": "attacker/repo", "output_format": "txt"})},
    )
    assert res.status_code == 422
    assert "Unknown model" in res.json()["detail"]


def test_unknown_language_is_rejected():
    import json as json_mod

    res = client.post(
        "/api/jobs",
        files=[("files", ("a.mp3", b"x", "audio/mpeg"))],
        data={"options": json_mod.dumps({"languages": ["zz"], "model": "tiny", "output_format": "txt"})},
    )
    assert res.status_code == 422
    assert "zz" in res.json()["detail"]


def test_request_from_another_site_is_refused():
    """multipart is CORS-safelisted, so the request must be blocked, not just
    have its response withheld."""
    res = client.get("/api/languages", headers={"Origin": "http://evil.example"})
    assert res.status_code == 403


def test_unknown_api_path_is_404_not_the_spa_shell():
    res = client.get("/api/nope")
    assert res.status_code == 404


@needs_built_frontend
def test_public_files_are_served_from_the_dist_root():
    """Vite copies public/ to the root of dist, not under /assets. Without an
    explicit branch those files get the HTML shell and render as broken."""
    res = client.get("/favicon.png")
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"


def test_path_traversal_through_the_spa_fallback_is_refused():
    res = client.get("/../backend/app/config.py")
    assert res.status_code in (404, 200)
    assert "TIMBRE" not in res.text


def test_local_paths_endpoint_is_absent_without_a_token():
    """Without the desktop token any page on the machine could name a path."""
    res = client.post(
        "/api/jobs/local",
        json={"paths": ["/etc/hosts"], "options": {"model": "tiny", "languages": [], "output_format": "txt"}},
    )
    assert res.status_code == 404


def test_local_paths_endpoint_accepts_real_files(tmp_path, monkeypatch):
    import importlib

    from fastapi.testclient import TestClient as TC

    import app.config
    import app.main

    monkeypatch.setenv("TIMBRE_TOKEN", "desk")
    importlib.reload(app.config)
    importlib.reload(app.routers.transcribe)
    importlib.reload(app.main)
    from app.routers import transcribe as router_mod

    monkeypatch.setattr(router_mod.manager, "start", lambda job_id: None)
    media = tmp_path / "clip.mp3"
    media.write_bytes(b"x" * 16)

    with TC(app.main.app) as c:
        headers = {"Authorization": "Bearer desk"}
        ok = c.post(
            "/api/jobs/local",
            json={"paths": [str(media)], "options": {"model": "tiny", "languages": [], "output_format": "txt"}},
            headers=headers,
        )
        assert ok.status_code == 200

        missing = c.post(
            "/api/jobs/local",
            json={
                "paths": [str(tmp_path / "gone.mp3")],
                "options": {"model": "tiny", "languages": [], "output_format": "txt"},
            },
            headers=headers,
        )
        assert missing.status_code == 400

        bad_model = c.post(
            "/api/jobs/local",
            json={
                "paths": [str(media)],
                "options": {"model": "evil/repo", "languages": [], "output_format": "txt"},
            },
            headers=headers,
        )
        assert bad_model.status_code == 422

    monkeypatch.delenv("TIMBRE_TOKEN")
    importlib.reload(app.config)
    importlib.reload(app.routers.transcribe)
    importlib.reload(app.main)


def test_desktop_origin_is_allowed_when_a_token_is_set():
    """The desktop frontend runs on Tauri's scheme, so every call is
    cross-origin. Without the header the webview refuses to read the reply and
    the app looks like it cannot reach its own server."""
    import importlib
    import os

    from fastapi.testclient import TestClient as TC

    import app.config
    import app.main
    import app.routers.transcribe

    os.environ["TIMBRE_TOKEN"] = "desk"
    importlib.reload(app.config)
    importlib.reload(app.routers.transcribe)
    importlib.reload(app.main)
    try:
        with TC(app.main.app) as c:
            res = c.get(
                "/api/health",
                headers={"Origin": "tauri://localhost", "Authorization": "Bearer desk"},
            )
            assert res.status_code == 200
            assert res.headers.get("access-control-allow-origin") == "tauri://localhost"
    finally:
        del os.environ["TIMBRE_TOKEN"]
        importlib.reload(app.config)
        importlib.reload(app.routers.transcribe)
        importlib.reload(app.main)


def test_packaged_build_writes_outside_the_bundle(tmp_path, monkeypatch):
    """A frozen build must not put uploads beside its own executable.

    Launched from a downloaded disk image, that directory is a volume sized to
    the app, so the first extracted wav fills it and every job fails with
    ENOSPC. Installed normally it would still be wrong: the bundle is code
    signed and is replaced on update.
    """
    import importlib

    import app.config

    monkeypatch.delenv("TIMBRE_DATA_DIR", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData" / "Local"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / ".local" / "share"))
    try:
        importlib.reload(app.config)
        bundle = Path(app.config.__file__).resolve().parent.parent
        assert bundle not in app.config.UPLOAD_DIR.parents
        assert tmp_path in app.config.UPLOAD_DIR.parents
    finally:
        monkeypatch.undo()
        importlib.reload(app.config)


def test_data_dir_env_var_still_wins_when_frozen(tmp_path, monkeypatch):
    import importlib

    import app.config

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setenv("TIMBRE_DATA_DIR", str(tmp_path / "chosen"))
    try:
        importlib.reload(app.config)
        assert app.config.DATA_DIR == tmp_path / "chosen"
    finally:
        monkeypatch.undo()
        importlib.reload(app.config)
