from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.network_check import NetworkCheck
from backend.app.services.network import TcpCheckResult


def create_host(client: TestClient) -> int:
    response = client.post(
        "/hosts",
        json={
            "hostname": "API-MONITOR-SERVER",
            "ip_address": "10.20.0.10",
            "operating_system": "Ubuntu 24.04",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_create_tcp_check(
    client: TestClient,
    db_session: Session,
) -> None:
    host_id = create_host(client)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=True,
            duration_ms=8.5,
            error=None,
        ),
    ) as mock_check:
        response = client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={
                "port": 443,
                "timeout": 0.5,
            },
        )

    assert response.status_code == 201

    data = response.json()

    assert data["host_id"] == host_id
    assert data["port"] == 443
    assert data["is_open"] is True
    assert data["duration_ms"] == 8.5
    assert data["error"] is None
    assert data["checked_at"] is not None

    persisted_check = db_session.scalar(
        select(NetworkCheck).where(
            NetworkCheck.id == data["id"],
        )
    )

    assert persisted_check is not None
    assert persisted_check.host_id == host_id
    assert persisted_check.port == 443

    mock_check.assert_called_once_with(
        host="10.20.0.10",
        port=443,
        timeout=0.5,
    )


def test_create_tcp_check_returns_not_found(
    client: TestClient,
) -> None:
    with patch("backend.app.services.monitoring.check_tcp_port") as mock_check:
        response = client.post(
            "/hosts/999999/checks/tcp",
            json={
                "port": 443,
            },
        )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }

    mock_check.assert_not_called()


def test_create_tcp_check_rejects_invalid_port(
    client: TestClient,
) -> None:
    with patch("backend.app.api.routes.network_checks.run_tcp_check") as mock_run:
        response = client.post(
            "/hosts/1/checks/tcp",
            json={
                "port": 70000,
            },
        )

    assert response.status_code == 422

    detail = response.json()["detail"]

    assert detail[0]["loc"] == ["body", "port"]
    assert detail[0]["type"] == "less_than_equal"

    mock_run.assert_not_called()


def test_create_tcp_check_rejects_invalid_timeout(
    client: TestClient,
) -> None:
    with patch("backend.app.api.routes.network_checks.run_tcp_check") as mock_run:
        response = client.post(
            "/hosts/1/checks/tcp",
            json={
                "port": 443,
                "timeout": 0,
            },
        )

    assert response.status_code == 422

    detail = response.json()["detail"]

    assert detail[0]["loc"] == ["body", "timeout"]
    assert detail[0]["type"] == "greater_than"

    mock_run.assert_not_called()
