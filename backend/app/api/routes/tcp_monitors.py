from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.host import Host
from backend.app.models.tcp_monitor import TcpMonitor
from backend.app.schemas.tcp_monitor import TcpMonitorCreate, TcpMonitorRead

router = APIRouter(
    prefix="/hosts/{host_id}/monitors/tcp",
    tags=["tcp-monitors"],
)

DbSession = Annotated[Session, Depends(get_db_session)]


@router.post(
    "",
    response_model=TcpMonitorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tcp_monitor(
    host_id: int,
    payload: TcpMonitorCreate,
    session: DbSession,
) -> TcpMonitor:
    host = session.get(Host, host_id)

    if host is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found.",
        )

    monitor = TcpMonitor(
        host_id=host_id,
        port=payload.port,
        timeout_seconds=payload.timeout_seconds,
        enabled=payload.enabled,
    )

    session.add(monitor)

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="TCP monitor already exists for this host and port.",
        ) from None

    session.refresh(monitor)

    return monitor
