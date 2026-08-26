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


def test_list_tcp_monitors(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    first_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
        },
    )
    second_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 22,
            "enabled": False,
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = client.get(
        f"/hosts/{host_id}/monitors/tcp",
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["port"] == 22
    assert data[0]["enabled"] is False
    assert data[1]["port"] == 443
    assert data[1]["enabled"] is True


def test_list_tcp_monitors_returns_empty_list(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    response = client.get(
        f"/hosts/{host_id}/monitors/tcp",
    )

    assert response.status_code == 200
    assert response.json() == []


def test_list_tcp_monitors_returns_not_found_for_missing_host(
    client: TestClient,
) -> None:
    response = client.get(
        "/hosts/999999/monitors/tcp",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }


def test_get_tcp_monitor(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    create_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
            "timeout_seconds": 2.0,
            "enabled": True,
        },
    )

    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]

    response = client.get(
        f"/hosts/{host_id}/monitors/tcp/{monitor_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == monitor_id
    assert data["host_id"] == host_id
    assert data["port"] == 443
    assert data["timeout_seconds"] == 2.0
    assert data["enabled"] is True


def test_get_tcp_monitor_returns_not_found_for_missing_host(
    client: TestClient,
) -> None:
    response = client.get(
        "/hosts/999999/monitors/tcp/1",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }


def test_get_tcp_monitor_returns_not_found_for_monitor_from_another_host(
    client: TestClient,
) -> None:
    first_host_id = create_test_host(client)

    monitor_response = client.post(
        f"/hosts/{first_host_id}/monitors/tcp",
        json={
            "port": 443,
        },
    )

    assert monitor_response.status_code == 201

    monitor_id = monitor_response.json()["id"]

    second_host_response = client.post(
        "/hosts",
        json={
            "hostname": "SECOND-TCP-MONITOR-SERVER",
            "ip_address": "10.80.0.20",
            "operating_system": "Debian 13",
        },
    )

    assert second_host_response.status_code == 201

    second_host_id = second_host_response.json()["id"]

    response = client.get(
        f"/hosts/{second_host_id}/monitors/tcp/{monitor_id}",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "TCP monitor not found.",
    }


def test_get_tcp_monitor_returns_not_found_for_missing_monitor(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    response = client.get(
        f"/hosts/{host_id}/monitors/tcp/999999",
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "TCP monitor not found.",
    }


def test_update_tcp_monitor_partial(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    create_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
            "timeout_seconds": 2.0,
            "enabled": True,
        },
    )

    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/hosts/{host_id}/monitors/tcp/{monitor_id}",
        json={
            "enabled": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == monitor_id
    assert data["host_id"] == host_id
    assert data["port"] == 443
    assert data["timeout_seconds"] == 2.0
    assert data["enabled"] is False


def test_update_tcp_monitor_returns_not_found_for_missing_monitor(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    response = client.patch(
        f"/hosts/{host_id}/monitors/tcp/999999",
        json={
            "enabled": False,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "TCP monitor not found.",
    }


def test_update_tcp_monitor_returns_conflict_for_duplicate_port(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    first_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 22,
        },
    )
    second_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    second_monitor_id = second_response.json()["id"]

    response = client.patch(
        f"/hosts/{host_id}/monitors/tcp/{second_monitor_id}",
        json={
            "port": 22,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "TCP monitor already exists for this host and port.",
    }


def test_update_tcp_monitor_returns_not_found_for_missing_host(
    client: TestClient,
) -> None:
    response = client.patch(
        "/hosts/999999/monitors/tcp/1",
        json={
            "enabled": False,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }


def test_update_tcp_monitor_rejects_invalid_port(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    create_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
        },
    )

    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/hosts/{host_id}/monitors/tcp/{monitor_id}",
        json={
            "port": 70000,
        },
    )

    assert response.status_code == 422


def test_update_tcp_monitor_rejects_invalid_timeout(
    client: TestClient,
) -> None:
    host_id = create_test_host(client)

    create_response = client.post(
        f"/hosts/{host_id}/monitors/tcp",
        json={
            "port": 443,
        },
    )

    assert create_response.status_code == 201

    monitor_id = create_response.json()["id"]

    response = client.patch(
        f"/hosts/{host_id}/monitors/tcp/{monitor_id}",
        json={
            "timeout_seconds": 0,
        },
    )

    assert response.status_code == 422
