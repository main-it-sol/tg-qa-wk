"""FastAPI application entrypoint."""

from fastapi import FastAPI

from .voice.ws import build_router


def create_app() -> FastAPI:
    app = FastAPI(title="Virtual Rabbi (sketch)")
    app.include_router(build_router())

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
