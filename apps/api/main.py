"""FastAPI application entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.routers import dimensions, health, reports, runs, samples
from apps.api.settings import settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup hooks (DB pool warmup, cache priming) go here.
    yield
    # Shutdown hooks.


def create_app() -> FastAPI:
    app = FastAPI(
        title="JS-RE-Bench API",
        version="0.1.0",
        description="Control plane for the JS/Web Reverse Engineering Benchmark Platform",
        lifespan=lifespan,
        contact={"name": "JS-RE-Bench Maintainers"},
        license_info={"name": "Apache-2.0"},
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(runs.router)
    app.include_router(samples.router)
    app.include_router(dimensions.router)
    app.include_router(reports.router)

    return app


app = create_app()


def main() -> None:
    """Convenience runner for ``python -m apps.api.main``."""
    import uvicorn

    uvicorn.run(
        "apps.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
