from unittest.mock import patch

import pytest

from backend.app.services.network import check_tcp_port


def test_check_tcp_port_open() -> None:
    with (
        patch("backend.app.services.network.create_connection") as mock_connection,
        patch(
            "backend.app.services.network.perf_counter",
            side_effect=[10.0, 10.012],
        ),
    ):
        result = check_tcp_port(
            host="127.0.0.1",
            port=443,
            timeout=0.5,
        )

    assert result.is_open is True
    assert result.duration_ms == pytest.approx(12.0)
    assert result.error is None

    mock_connection.assert_called_once_with(
        ("127.0.0.1", 443),
        timeout=0.5,
    )


def test_check_tcp_port_timeout() -> None:
    with (
        patch(
            "backend.app.services.network.create_connection",
            side_effect=TimeoutError("timed out"),
        ),
        patch(
            "backend.app.services.network.perf_counter",
            side_effect=[20.0, 21.0],
        ),
    ):
        result = check_tcp_port(
            host="192.0.2.1",
            port=22,
            timeout=1.0,
        )

    assert result.is_open is False
    assert result.duration_ms == pytest.approx(1000.0)
    assert result.error == "timed out"


def test_check_tcp_port_rejects_invalid_port() -> None:
    with pytest.raises(
        ValueError,
        match=r"Port must be between 1 and 65535\.",
    ):
        check_tcp_port(
            host="127.0.0.1",
            port=70000,
        )


def test_check_tcp_port_rejects_invalid_timeout() -> None:
    with pytest.raises(
        ValueError,
        match=r"Timeout must be greater than zero\.",
    ):
        check_tcp_port(
            host="127.0.0.1",
            port=443,
            timeout=0,
        )
