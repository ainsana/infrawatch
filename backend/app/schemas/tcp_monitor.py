from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TcpMonitorCreate(BaseModel):
    port: int = Field(ge=1, le=65535)
    timeout_seconds: float = Field(default=1.0, gt=0, le=30)
    enabled: bool = True


class TcpMonitorUpdate(BaseModel):
    port: int | None = Field(default=None, ge=1, le=65535)
    timeout_seconds: float | None = Field(default=None, gt=0, le=30)
    enabled: bool | None = None


class TcpMonitorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    host_id: int
    port: int
    timeout_seconds: float
    enabled: bool
    created_at: datetime
    updated_at: datetime
