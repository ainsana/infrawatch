from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.services.host_health import (
    evaluate_host_status,
    refresh_all_host_statuses,
    refresh_host_status,
)


def test_host_status_is_unknown_when_never_seen() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)

    status = evaluate_host_status(
        last_seen_at=None,
        now=now,
    )

    assert status == "unknown"


def test_host_status_is_online_when_recently_seen() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)
    last_seen_at = now - timedelta(minutes=2)

    status = evaluate_host_status(
        last_seen_at=last_seen_at,
        now=now,
    )

    assert status == "online"


def test_host_status_is_offline_when_last_seen_is_stale() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)
    last_seen_at = now - timedelta(minutes=10)

    status = evaluate_host_status(
        last_seen_at=last_seen_at,
        now=now,
    )

    assert status == "offline"


def test_host_status_is_online_at_exact_threshold() -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)
    last_seen_at = now - timedelta(minutes=5)

    status = evaluate_host_status(
        last_seen_at=last_seen_at,
        now=now,
        offline_after=timedelta(minutes=5),
    )

    assert status == "online"


def test_host_status_rejects_invalid_threshold() -> None:
    with pytest.raises(
        ValueError,
        match="Offline threshold must be greater than zero.",
    ):
        evaluate_host_status(
            last_seen_at=None,
            offline_after=timedelta(0),
        )


def create_health_test_host(
    db_session: Session,
    *,
    last_seen_at: datetime | None,
) -> Host:
    host = Host(
        hostname="HEALTH-SERVER",
        ip_address="10.30.0.10",
        operating_system="Ubuntu 24.04",
        last_seen_at=last_seen_at,
    )

    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)

    return host


def test_refresh_host_status_marks_recent_host_online(
    db_session: Session,
) -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)

    host = create_health_test_host(
        db_session,
        last_seen_at=now - timedelta(minutes=2),
    )

    refreshed_host = refresh_host_status(
        session=db_session,
        host_id=host.id,
        now=now,
    )

    assert refreshed_host is not None
    assert refreshed_host.status == "online"


def test_refresh_host_status_marks_stale_host_offline(
    db_session: Session,
) -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)

    host = create_health_test_host(
        db_session,
        last_seen_at=now - timedelta(minutes=10),
    )

    host.status = "online"
    db_session.commit()

    refreshed_host = refresh_host_status(
        session=db_session,
        host_id=host.id,
        now=now,
    )

    assert refreshed_host is not None
    assert refreshed_host.status == "offline"


def test_refresh_host_status_returns_none_for_missing_host(
    db_session: Session,
) -> None:
    refreshed_host = refresh_host_status(
        session=db_session,
        host_id=999999,
    )

    assert refreshed_host is None


def test_refresh_host_status_keeps_matching_status(
    db_session: Session,
) -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)

    host = create_health_test_host(
        db_session,
        last_seen_at=now - timedelta(minutes=2),
    )

    host.status = "online"
    db_session.commit()

    refreshed_host = refresh_host_status(
        session=db_session,
        host_id=host.id,
        now=now,
    )

    assert refreshed_host is not None
    assert refreshed_host.status == "online"


def test_refresh_all_host_statuses_updates_multiple_hosts(
    db_session: Session,
) -> None:
    now = datetime(2026, 8, 24, 19, 0, tzinfo=UTC)

    recent_host = Host(
        hostname="RECENT-SERVER",
        ip_address="10.50.0.10",
        operating_system="Ubuntu 24.04",
        status="unknown",
        last_seen_at=now - timedelta(minutes=2),
    )

    stale_host = Host(
        hostname="STALE-SERVER",
        ip_address="10.50.0.20",
        operating_system="Windows Server 2022",
        status="online",
        last_seen_at=now - timedelta(minutes=10),
    )

    unchanged_host = Host(
        hostname="UNKNOWN-SERVER",
        ip_address="10.50.0.30",
        operating_system="Debian 13",
        status="unknown",
        last_seen_at=None,
    )

    db_session.add_all(
        [
            recent_host,
            stale_host,
            unchanged_host,
        ]
    )
    db_session.commit()

    changed_count = refresh_all_host_statuses(
        session=db_session,
        now=now,
    )

    assert changed_count == 2
    assert recent_host.status == "online"
    assert stale_host.status == "offline"
    assert unchanged_host.status == "unknown"


def test_refresh_all_host_statuses_returns_zero_when_no_hosts(
    db_session: Session,
) -> None:
    changed_count = refresh_all_host_statuses(
        session=db_session,
    )

    assert changed_count == 0
