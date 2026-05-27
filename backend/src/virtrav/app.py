"""FastAPI application entrypoint."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from .voice.ws import build_router

STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


def create_app() -> FastAPI:
    app = FastAPI(title="Virtual Rabbi (sketch)")
    app.include_router(build_router())

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(INDEX_HTML, media_type="text/html")

    return app


app = create_app()
