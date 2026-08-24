from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.tcp_monitor import TcpMonitor


def test_tcp_monitor_uses_defaults(
    db_session: Session,
) -> None:
    host = Host(
        hostname="MONITOR-DEFAULTS-SERVER",
        ip_address="10.70.0.10",
        operating_system="Ubuntu 24.04",
    )

    db_session.add(host)
    db_session.flush()

    monitor = TcpMonitor(
        host_id=host.id,
        port=443,
    )

    db_session.add(monitor)
    db_session.flush()
    db_session.refresh(monitor)

    assert monitor.id is not None
    assert monitor.host_id == host.id
    assert monitor.port == 443
    assert monitor.timeout_seconds == 1.0
    assert monitor.enabled is True
    assert monitor.created_at is not None
    assert monitor.updated_at is not None


def test_deleting_host_cascades_to_tcp_monitor(
    db_session: Session,
) -> None:
    host = Host(
        hostname="MONITOR-CASCADE-SERVER",
        ip_address="10.70.0.20",
        operating_system="Windows Server 2022",
    )

    db_session.add(host)
    db_session.flush()

    monitor = TcpMonitor(
        host_id=host.id,
        port=3389,
    )

    db_session.add(monitor)
    db_session.flush()

    monitor_id = monitor.id

    db_session.delete(host)
    db_session.flush()

    deleted_monitor = db_session.scalar(
        select(TcpMonitor).where(
            TcpMonitor.id == monitor_id,
        )
    )

    assert deleted_monitor is None
