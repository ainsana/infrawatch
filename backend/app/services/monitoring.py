import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.network_check import NetworkCheck
from backend.app.models.tcp_monitor import TcpMonitor
from backend.app.services.network import check_tcp_port

logger = logging.getLogger(__name__)


def run_tcp_check(
    session: Session,
    host_id: int,
    port: int,
    timeout: float = 1.0,
) -> NetworkCheck | None:
    host = session.get(Host, host_id)

    if host is None:
        return None

    result = check_tcp_port(
        host=host.ip_address,
        port=port,
        timeout=timeout,
    )

    network_check = NetworkCheck(
        host_id=host.id,
        port=port,
        is_open=result.is_open,
        duration_ms=result.duration_ms,
        error=result.error,
    )

    session.add(network_check)
    if result.is_open:
        host.status = "online"
        host.last_seen_at = datetime.now(UTC)
    session.commit()
    session.refresh(network_check)

    return network_check


def run_enabled_tcp_monitors(
    session: Session,
) -> int:
    statement = select(TcpMonitor).where(TcpMonitor.enabled.is_(True)).order_by(TcpMonitor.id)

    monitors = list(session.scalars(statement).all())

    executed_count = 0

    for monitor in monitors:
        try:
            network_check = run_tcp_check(
                session=session,
                host_id=monitor.host_id,
                port=monitor.port,
                timeout=monitor.timeout_seconds,
            )
        except Exception:
            session.rollback()
            logger.exception(
                "TCP monitor execution failed: monitor_id=%s host_id=%s port=%s",
                monitor.id,
                monitor.host_id,
                monitor.port,
            )
            continue

        if network_check is not None:
            executed_count += 1

    return executed_count
