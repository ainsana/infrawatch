from fastapi.testclient import TestClient


def create_test_host(client: TestClient) -> int:
    response = client.post(
        "/hosts",
        json={
            "hostname": "TCP-MONITOR-SERVER",
            "ip_address": "10.80.0.10",
            "operating_system": "Ubuntu 24.04",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def test_create_tcp_monitor(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
            "timeout_seconds": 2.5,
            "enabled": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["host_id"] == host_id
    assert data["port"] == 443
    assert data["timeout_seconds"] == 2.5
    assert data["enabled"] is True
    assert data["id"] is not None
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_create_tcp_monitor_returns_not_found_for_missing_host(
    client: TestClient,
) -> None:
    response = client.post(
        "/hosts/999999/monitors/tcp",
        json={
            "port": 443,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }


def test_create_tcp_monitor_returns_conflict_for_duplicate_port(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    first_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
        },
    )

    assert first_response.status_code == 201

    duplicate_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
        },
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {
        "detail": "TCP monitor already exists for this host and port.",
    }


def test_create_tcp_monitor_rejects_invalid_port(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 70000,
        },
    )

    assert response.status_code == 422


def test_create_tcp_monitor_rejects_invalid_timeout(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
            "timeout_seconds": 0,
        },
    )

    assert response.status_code == 422
