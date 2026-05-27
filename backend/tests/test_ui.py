"""Tests for the static dev UI served at ``/``."""

from __future__ import annotations

from fastapi.testclient import TestClient

from virtrav.app import INDEX_HTML, create_app


def test_index_file_exists_on_disk() -> None:
    assert INDEX_HTML.is_file(), f"missing UI file: {INDEX_HTML}"


def test_index_route_serves_html() -> None:
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    body = resp.text
    assert "<html" in body.lower()


def test_index_references_voice_websocket_and_ui_hooks() -> None:
    app = create_app()
    with TestClient(app) as client:
        body = client.get("/").text
    # The page must point at the real WS path the backend exposes.
    assert "/voice" in body
    # Core UI affordances the user needs to "see real progress".
    for hook in (
        'id="state"',
        'id="transcript"',
        'id="log"',
        'id="btn-connect"',
        'id="btn-talk"',
        'id="btn-interrupt"',
    ):
        assert hook in body, f"UI hook missing: {hook}"


def test_healthz_still_works() -> None:
    """Sanity: adding the index route did not break the existing health probe."""
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
