from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.network_check import NetworkCheck
from backend.app.models.tcp_monitor import TcpMonitor
from backend.app.services.monitoring import (
    run_enabled_tcp_monitors,
    run_monitoring_cycle,
    run_tcp_check,
)
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

    assert host.status == "online"
    assert host.last_seen_at is not None

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


def test_run_tcp_check_failure_does_not_mark_host_offline(
    db_session: Session,
) -> None:
    host = create_test_host(db_session)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=True,
            duration_ms=5.0,
            error=None,
        ),
    ):
        run_tcp_check(
            session=db_session,
            host_id=host.id,
            port=443,
        )

    previous_last_seen_at = host.last_seen_at

    assert host.status == "online"
    assert previous_last_seen_at is not None

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
        )

    assert network_check is not None
    assert network_check.is_open is False
    assert host.status == "online"
    assert host.last_seen_at == previous_last_seen_at


def test_run_enabled_tcp_monitors_runs_only_enabled_monitors(
    db_session: Session,
) -> None:
    host = create_test_host(db_session)

    enabled_monitor = TcpMonitor(
        host_id=host.id,
        port=443,
        timeout_seconds=2.0,
        enabled=True,
    )
    disabled_monitor = TcpMonitor(
        host_id=host.id,
        port=22,
        timeout_seconds=3.0,
        enabled=False,
    )

    db_session.add_all(
        [
            enabled_monitor,
            disabled_monitor,
        ]
    )
    db_session.commit()

    with patch(
        "backend.app.services.monitoring.run_tcp_check",
    ) as mock_run_tcp_check:
        mock_run_tcp_check.return_value = NetworkCheck(
            host_id=host.id,
            port=443,
            is_open=True,
            duration_ms=5.0,
            error=None,
        )

        executed_count = run_enabled_tcp_monitors(
            session=db_session,
        )

    assert executed_count == 1

    mock_run_tcp_check.assert_called_once_with(
        session=db_session,
        host_id=host.id,
        port=443,
        timeout=2.0,
    )


def test_run_enabled_tcp_monitors_returns_zero_when_no_enabled_monitors(
    db_session: Session,
) -> None:
    host = create_test_host(db_session)

    monitor = TcpMonitor(
        host_id=host.id,
        port=443,
        enabled=False,
    )

    db_session.add(monitor)
    db_session.commit()

    with patch(
        "backend.app.services.monitoring.run_tcp_check",
    ) as mock_run_tcp_check:
        executed_count = run_enabled_tcp_monitors(
            session=db_session,
        )

    assert executed_count == 0
    mock_run_tcp_check.assert_not_called()


def test_run_enabled_tcp_monitors_persists_network_check(
    db_session: Session,
) -> None:
    host = create_test_host(db_session)

    monitor = TcpMonitor(
        host_id=host.id,
        port=443,
        timeout_seconds=2.5,
        enabled=True,
    )

    db_session.add(monitor)
    db_session.commit()

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=True,
            duration_ms=7.5,
            error=None,
        ),
    ) as mock_check:
        executed_count = run_enabled_tcp_monitors(
            session=db_session,
        )

    assert executed_count == 1

    persisted_check = db_session.scalar(
        select(NetworkCheck).where(
            NetworkCheck.host_id == host.id,
            NetworkCheck.port == 443,
        )
    )

    assert persisted_check is not None
    assert persisted_check.is_open is True
    assert persisted_check.duration_ms == 7.5
    assert persisted_check.error is None

    assert host.status == "online"
    assert host.last_seen_at is not None

    mock_check.assert_called_once_with(
        host="10.10.0.10",
        port=443,
        timeout=2.5,
    )


def test_run_enabled_tcp_monitors_continues_after_monitor_error(
    db_session: Session,
) -> None:
    host = create_test_host(db_session)

    first_monitor = TcpMonitor(
        host_id=host.id,
        port=22,
        enabled=True,
    )
    second_monitor = TcpMonitor(
        host_id=host.id,
        port=443,
        enabled=True,
    )

    db_session.add_all(
        [
            first_monitor,
            second_monitor,
        ]
    )
    db_session.commit()

    successful_check = NetworkCheck(
        host_id=host.id,
        port=443,
        is_open=True,
        duration_ms=5.0,
        error=None,
    )

    with patch(
        "backend.app.services.monitoring.run_tcp_check",
        side_effect=[
            RuntimeError("unexpected monitoring error"),
            successful_check,
        ],
    ) as mock_run_tcp_check:
        executed_count = run_enabled_tcp_monitors(
            session=db_session,
        )

    assert executed_count == 1
    assert mock_run_tcp_check.call_count == 2


def test_run_enabled_tcp_monitors_logs_monitor_error(
    db_session: Session,
    caplog,
) -> None:
    host = create_test_host(db_session)

    monitor = TcpMonitor(
        host_id=host.id,
        port=443,
        enabled=True,
    )

    db_session.add(monitor)
    db_session.commit()

    with patch(
        "backend.app.services.monitoring.run_tcp_check",
        side_effect=RuntimeError("unexpected monitoring error"),
    ):
        executed_count = run_enabled_tcp_monitors(
            session=db_session,
        )

    assert executed_count == 0
    assert "TCP monitor execution failed" in caplog.text


def test_run_monitoring_cycle_uses_own_database_session(
    db_session: Session,
) -> None:
    with (
        patch(
            "backend.app.services.monitoring.SessionLocal",
        ) as mock_session_local,
        patch(
            "backend.app.services.monitoring.run_enabled_tcp_monitors",
            return_value=3,
        ) as mock_run_enabled_tcp_monitors,
    ):
        mock_session_local.return_value.__enter__.return_value = db_session

        executed_count = run_monitoring_cycle()

    assert executed_count == 3

    mock_session_local.assert_called_once_with()
    mock_run_enabled_tcp_monitors.assert_called_once_with(
        session=db_session,
    )
