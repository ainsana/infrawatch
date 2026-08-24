from sqlalchemy.orm import Session

from backend.app.models.host import Host
from backend.app.models.network_check import NetworkCheck
from backend.app.services.network import check_tcp_port


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
    session.commit()
    session.refresh(network_check)

    return network_check
