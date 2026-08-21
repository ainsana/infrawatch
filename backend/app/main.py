from fastapi import FastAPI

app = FastAPI(
    title="InfraWatch API",
    version="0.0.1",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "infrawatch-api",
        "version": "0.0.1",
    }