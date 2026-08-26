import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI

from backend.app.api.routes.hosts import router as hosts_router
from backend.app.api.routes.network_checks import router as network_checks_router
from backend.app.api.routes.tcp_monitors import router as tcp_monitors_router
from backend.app.core.config import get_settings
from backend.app.services.scheduler import run_monitoring_scheduler


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None]:
    settings = get_settings()

    scheduler_task = asyncio.create_task(
        run_monitoring_scheduler(
            interval_seconds=settings.monitoring_interval_seconds,
        )
    )

    try:
        yield
    finally:
        scheduler_task.cancel()

        with suppress(asyncio.CancelledError):
            await scheduler_task


app = FastAPI(
    title="InfraWatch API",
    version="0.0.1",
    lifespan=lifespan,
)

app.include_router(hosts_router)
app.include_router(network_checks_router)
app.include_router(tcp_monitors_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "infrawatch-api",
        "version": "0.0.1",
    }
