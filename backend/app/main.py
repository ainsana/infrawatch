from fastapi import FastAPI

from backend.app.api.routes.hosts import router as hosts_router
from backend.app.api.routes.network_checks import router as network_checks_router

app = FastAPI(
    title="InfraWatch API",
    version="0.0.1",
)

app.include_router(hosts_router)
app.include_router(network_checks_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "infrawatch-api",
        "version": "0.0.1",
    }
