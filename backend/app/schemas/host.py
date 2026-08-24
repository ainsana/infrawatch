from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HostCreate(BaseModel):
    hostname: str
    ip_address: str
    operating_system: str


class HostUpdate(BaseModel):
    hostname: str | None = None
    ip_address: str | None = None
    operating_system: str | None = None


class HostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hostname: str
    ip_address: str
    operating_system: str
    status: str
    created_at: datetime
    updated_at: datetime
