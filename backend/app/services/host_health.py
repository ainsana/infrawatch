from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host


def evaluate_host_status(
    last_seen_at: datetime | None,
    *,
    now: datetime | None = None,
    offline_after: timedelta = timedelta(minutes=5),
) -> str:
    if offline_after <= timedelta(0):
        raise ValueError("Offline threshold must be greater than zero.")

    if last_seen_at is None:
        return "unknown"

    current_time = now or datetime.now(UTC)

    if last_seen_at.tzinfo is None:
        raise ValueError("Last seen timestamp must be timezone-aware.")

    if current_time.tzinfo is None:
        raise ValueError("Current timestamp must be timezone-aware.")

    elapsed = current_time - last_seen_at

    if elapsed <= offline_after:
        return "online"

    return "offline"


def refresh_host_status(
    session: Session,
    host_id: int,
    *,
    now: datetime | None = None,
    offline_after: timedelta = timedelta(minutes=5),
) -> Host | None:
    host = session.get(Host, host_id)

    if host is None:
        return None

    new_status = evaluate_host_status(
        last_seen_at=host.last_seen_at,
        now=now,
        offline_after=offline_after,
    )

    if host.status != new_status:
        host.status = new_status
        session.commit()
        session.refresh(host)

    return host


def refresh_all_host_statuses(
    session: Session,
    *,
    now: datetime | None = None,
    offline_after: timedelta = timedelta(minutes=5),
) -> int:
    current_time = now or datetime.now(UTC)

    hosts = list(
        session.scalars(
            select(Host).order_by(Host.id),
        ).all()
    )

    changed_count = 0

    for host in hosts:
        new_status = evaluate_host_status(
            last_seen_at=host.last_seen_at,
            now=current_time,
            offline_after=offline_after,
        )

        if host.status != new_status:
            host.status = new_status
            changed_count += 1

    if changed_count > 0:
        session.commit()

    return changed_count
