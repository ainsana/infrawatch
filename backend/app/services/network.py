from dataclasses import dataclass
from socket import create_connection
from time import perf_counter


@dataclass(frozen=True, slots=True)
class TcpCheckResult:
    is_open: bool
    duration_ms: float
    error: str | None


def check_tcp_port(
    host: str,
    port: int,
    timeout: float = 1.0,
) -> TcpCheckResult:
    if not 1 <= port <= 65535:
        raise ValueError("Port must be between 1 and 65535.")

    if timeout <= 0:
        raise ValueError("Timeout must be greater than zero.")

    started_at = perf_counter()

    try:
        with create_connection((host, port), timeout=timeout):
            duration_ms = (perf_counter() - started_at) * 1000

            return TcpCheckResult(
                is_open=True,
                duration_ms=duration_ms,
                error=None,
            )
    except OSError as exc:
        duration_ms = (perf_counter() - started_at) * 1000

        return TcpCheckResult(
            is_open=False,
            duration_ms=duration_ms,
            error=str(exc),
        )
