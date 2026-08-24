from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.network_check import NetworkCheck
from backend.app.services.monitoring import run_tcp_check
from backend.app.services.network import TcpCheckResult


def create_test_host(db_session: Session) -> Host:
    host = Host(
        hostname="MONITOR-SERVER",
        ip_address="10.10.0.10",
        operating_system="Ubuntu 24.04",
    )

    db_session.add(host)
    db_session.commit()
    db_session.refresh(host)

    return host


def test_run_tcp_check_persists_open_result(
    db_session: Session,
) -> None:
    host = create_test_host(db_session)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=True,
            duration_ms=12.5,
            error=None,
        ),
    ) as mock_check:
        network_check = run_tcp_check(
            session=db_session,
            host_id=host.id,
            port=443,
            timeout=0.5,
        )

    assert network_check is not None
    assert network_check.host_id == host.id
    assert network_check.port == 443
    assert network_check.is_open is True
    assert network_check.duration_ms == 12.5
    assert network_check.error is None
    assert network_check.checked_at is not None

    persisted_check = db_session.scalar(
        select(NetworkCheck).where(
            NetworkCheck.id == network_check.id,
        )
    )

    assert persisted_check is not None
    assert persisted_check.id == network_check.id

    mock_check.assert_called_once_with(
        host="10.10.0.10",
        port=443,
        timeout=0.5,
    )


def test_run_tcp_check_persists_failed_result(
    db_session: Session,
) -> None:
    host = create_test_host(db_session)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=False,
            duration_ms=1000.0,
            error="timed out",
        ),
    ):
        network_check = run_tcp_check(
            session=db_session,
            host_id=host.id,
            port=22,
            timeout=1.0,
        )

    assert network_check is not None
    assert network_check.is_open is False
    assert network_check.duration_ms == 1000.0
    assert network_check.error == "timed out"


def test_run_tcp_check_returns_none_for_missing_host(
    db_session: Session,
) -> None:
    with patch("backend.app.services.monitoring.check_tcp_port") as mock_check:
        network_check = run_tcp_check(
            session=db_session,
            host_id=999999,
            port=443,
        )

    assert network_check is None
    mock_check.assert_not_called()
