from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TcpCheckRequest(BaseModel):
    port: int = Field(ge=1, le=65535)
    timeout: float = Field(default=1.0, gt=0, le=30)


class NetworkCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host_id: int
    port: int
    is_open: bool
    duration_ms: float
    error: str | None
    checked_at: datetime
