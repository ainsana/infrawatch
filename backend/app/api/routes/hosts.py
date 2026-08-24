from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.database import get_db_session
from backend.app.models.host import Host
from backend.app.schemas.host import HostCreate, HostRead, HostUpdate

router = APIRouter(
    prefix="/hosts",
    tags=["hosts"],
)

DbSession = Annotated[Session, Depends(get_db_session)]
Offset = Annotated[int, Query(ge=0)]
Limit = Annotated[int, Query(ge=1, le=100)]


@router.post(
    "",
    response_model=HostRead,
    status_code=status.HTTP_201_CREATED,
)
def create_host(payload: HostCreate, session: DbSession) -> Host:
    host = Host(
        hostname=payload.hostname,
        ip_address=payload.ip_address,
        operating_system=payload.operating_system,
    )

    session.add(host)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A host with this hostname already exists.",
        ) from exc

    session.refresh(host)

    return host


@router.get(
    "",
    response_model=list[HostRead],
)
def list_hosts(
    session: DbSession,
    offset: Offset = 0,
    limit: Limit = 100,
) -> list[Host]:
    statement = select(Host).order_by(Host.id).offset(offset).limit(limit)

    return list(session.scalars(statement).all())


@router.get(
    "/{host_id}",
    response_model=HostRead,
)
def get_host(host_id: int, session: DbSession) -> Host:
    host = session.get(Host, host_id)

    if host is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found.",
        )

    return host


@router.patch(
    "/{host_id}",
    response_model=HostRead,
)
def update_host(
    host_id: int,
    payload: HostUpdate,
    session: DbSession,
) -> Host:
    host = session.get(Host, host_id)

    if host is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(host, field, value)

    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A host with this hostname already exists.",
        ) from exc

    session.refresh(host)

    return host


@router.delete(
    "/{host_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_host(host_id: int, session: DbSession) -> None:
    host = session.get(Host, host_id)

    if host is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host not found.",
        )

    session.delete(host)
    session.commit()
