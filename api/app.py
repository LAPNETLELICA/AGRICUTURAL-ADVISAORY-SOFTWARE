"""FastAPI application factory."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import mobile, sms, system
from engine import __version__
from engine.bootstrap import ApplicationContainer, build_container
from engine.config import Settings
from engine.exceptions import CropNotFoundError


def create_app(
    settings: Settings | None = None,
    container: ApplicationContainer | None = None,
) -> FastAPI:
    resolved_settings = settings or Settings.from_env()
    resolved_container = container or build_container(resolved_settings)
    app = FastAPI(
        title="Crop-Centered Agricultural Advisory API",
        version=__version__,
        description=(
            "Explainable rule-based advisory engine. Demo knowledge is not production agronomy."
        ),
    )
    app.state.container = resolved_container
    if resolved_settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(resolved_settings.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        )

    @app.exception_handler(CropNotFoundError)
    async def crop_not_found(_: Request, exc: CropNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def invalid_state(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(mobile.router)
    app.include_router(sms.router)
    app.include_router(system.router)

    @app.get("/", include_in_schema=False)
    def root() -> dict[str, str]:
        return {"service": app.title, "docs": "/docs", "health": "/api/v1/health"}

    return app


app = create_app()


def run() -> None:
    """Run the API with environment-backed settings."""
    settings = Settings.from_env()
    uvicorn.run(
        "api.app:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    run()
