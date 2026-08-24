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


def test_list_network_checks(
    client: TestClient,
) -> None:
    host_id = create_host(client)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        side_effect=[
            TcpCheckResult(
                is_open=True,
                duration_ms=5.0,
                error=None,
            ),
            TcpCheckResult(
                is_open=False,
                duration_ms=1000.0,
                error="timed out",
            ),
            TcpCheckResult(
                is_open=True,
                duration_ms=7.0,
                error=None,
            ),
        ],
    ):
        first_response = client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 22},
        )
        second_response = client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 80},
        )
        third_response = client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 443},
        )

    response = client.get(f"/hosts/{host_id}/checks")

    assert response.status_code == 200

    data = response.json()

    assert [item["id"] for item in data] == [
        third_response.json()["id"],
        second_response.json()["id"],
        first_response.json()["id"],
    ]

    assert [item["port"] for item in data] == [
        443,
        80,
        22,
    ]


def test_list_network_checks_pagination(
    client: TestClient,
) -> None:
    host_id = create_host(client)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=True,
            duration_ms=5.0,
            error=None,
        ),
    ):
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 22},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 80},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 443},
        )

    response = client.get(f"/hosts/{host_id}/checks?limit=1&offset=1")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["port"] == 80


def test_list_network_checks_returns_empty_list(
    client: TestClient,
) -> None:
    host_id = create_host(client)

    response = client.get(f"/hosts/{host_id}/checks")

    assert response.status_code == 200
    assert response.json() == []


def test_list_network_checks_returns_not_found(
    client: TestClient,
) -> None:
    response = client.get("/hosts/999999/checks")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }


def test_list_network_checks_filters_by_port(
    client: TestClient,
) -> None:
    host_id = create_host(client)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=True,
            duration_ms=5.0,
            error=None,
        ),
    ):
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 22},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 443},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 443},
        )

    response = client.get(f"/hosts/{host_id}/checks?port=443")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert all(item["port"] == 443 for item in data)


def test_list_network_checks_filters_by_open_status(
    client: TestClient,
) -> None:
    host_id = create_host(client)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        side_effect=[
            TcpCheckResult(
                is_open=True,
                duration_ms=5.0,
                error=None,
            ),
            TcpCheckResult(
                is_open=False,
                duration_ms=1000.0,
                error="timed out",
            ),
            TcpCheckResult(
                is_open=False,
                duration_ms=1000.0,
                error="timed out",
            ),
        ],
    ):
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 22},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 80},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 443},
        )

    response = client.get(f"/hosts/{host_id}/checks?is_open=false")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert all(item["is_open"] is False for item in data)


def test_list_network_checks_combines_filters(
    client: TestClient,
) -> None:
    host_id = create_host(client)

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        side_effect=[
            TcpCheckResult(
                is_open=True,
                duration_ms=5.0,
                error=None,
            ),
            TcpCheckResult(
                is_open=False,
                duration_ms=1000.0,
                error="timed out",
            ),
            TcpCheckResult(
                is_open=False,
                duration_ms=1000.0,
                error="timed out",
            ),
        ],
    ):
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 22},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 22},
        )
        client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={"port": 443},
        )

    response = client.get(f"/hosts/{host_id}/checks?port=22&is_open=false")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["port"] == 22
    assert data[0]["is_open"] is False


def test_list_network_checks_rejects_invalid_port_filter(
    client: TestClient,
) -> None:
    response = client.get("/hosts/1/checks?port=70000")

    assert response.status_code == 422

    detail = response.json()["detail"]

    assert detail[0]["loc"] == ["query", "port"]
    assert detail[0]["type"] == "less_than_equal"


def test_successful_tcp_check_updates_host_api_state(
    client: TestClient,
) -> None:
    host_id = create_host(client)

    before_response = client.get(f"/hosts/{host_id}")

    assert before_response.status_code == 200
    assert before_response.json()["status"] == "unknown"
    assert before_response.json()["last_seen_at"] is None

    with patch(
        "backend.app.services.monitoring.check_tcp_port",
        return_value=TcpCheckResult(
            is_open=True,
            duration_ms=4.5,
            error=None,
        ),
    ):
        check_response = client.post(
            f"/hosts/{host_id}/checks/tcp",
            json={
                "port": 443,
            },
        )

    assert check_response.status_code == 201

    after_response = client.get(f"/hosts/{host_id}")

    assert after_response.status_code == 200

    data = after_response.json()

    assert data["status"] == "online"
    assert data["last_seen_at"] is not None
