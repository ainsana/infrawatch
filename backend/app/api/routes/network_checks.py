from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.network_check import NetworkCheck
from backend.app.schemas.network_check import NetworkCheckRead, TcpCheckRequest
from backend.app.services.monitoring import run_tcp_check

router = APIRouter(
    prefix="/hosts/{host_id}/checks",
    tags=["network-checks"],
)

DbSession = Annotated[Session, Depends(get_db_session)]


@router.post(
    "/tcp",
    response_model=NetworkCheckRead,
    status_code=status.HTTP_201_CREATED,
)
def create_tcp_check(
    host_id: int,
    payload: TcpCheckRequest,
    session: DbSession,
) -> NetworkCheck:
    network_check = run_tcp_check(
        session=session,
        host_id=host_id,
        port=payload.port,
        timeout=payload.timeout,
    )

    if network_check is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found.",
        )

    return network_check
