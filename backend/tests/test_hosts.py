from fastapi.testclient import TestClient


def create_test_host(
    client: TestClient,
    hostname: str,
    ip_address: str,
    operating_system: str = "Ubuntu 24.04",
):
    return client.post(
        "/hosts",
        json={
            "hostname": hostname,
            "ip_address": ip_address,
            "operating_system": operating_system,
        },
    )


def test_create_host(client: TestClient) -> None:
    response = create_test_host(
        client,
        hostname="TEST-SERVER01",
        ip_address="10.0.0.10",
    )

    assert response.status_code == 201

    data = response.json()

    assert isinstance(data["id"], int)
    assert data["hostname"] == "TEST-SERVER01"
    assert data["ip_address"] == "10.0.0.10"
    assert data["operating_system"] == "Ubuntu 24.04"
    assert data["status"] == "unknown"
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_duplicate_hostname_returns_conflict(client: TestClient) -> None:
    first_response = create_test_host(
        client,
        hostname="DUPLICATE-SERVER",
        ip_address="10.0.0.20",
    )

    assert first_response.status_code == 201

    duplicate_response = create_test_host(
        client,
        hostname="DUPLICATE-SERVER",
        ip_address="10.0.0.21",
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json() == {"detail": "A host with this hostname already exists."}


def test_list_hosts(client: TestClient) -> None:
    create_test_host(client, "SERVER-A", "10.0.1.10")
    create_test_host(client, "SERVER-B", "10.0.1.20")

    response = client.get("/hosts")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert [host["hostname"] for host in data] == [
        "SERVER-A",
        "SERVER-B",
    ]


def test_list_hosts_pagination(client: TestClient) -> None:
    create_test_host(client, "SERVER-A", "10.0.2.10")
    create_test_host(client, "SERVER-B", "10.0.2.20")
    create_test_host(client, "SERVER-C", "10.0.2.30")

    first_page = client.get("/hosts?limit=1&offset=0")
    second_page = client.get("/hosts?limit=1&offset=1")

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    assert len(first_page.json()) == 1
    assert len(second_page.json()) == 1

    assert first_page.json()[0]["hostname"] == "SERVER-A"
    assert second_page.json()[0]["hostname"] == "SERVER-B"


def test_list_hosts_rejects_excessive_limit(client: TestClient) -> None:
    response = client.get("/hosts?limit=1000")

    assert response.status_code == 422

    detail = response.json()["detail"]

    assert detail[0]["loc"] == ["query", "limit"]
    assert detail[0]["type"] == "less_than_equal"


def test_each_test_starts_with_empty_database(client: TestClient) -> None:
    response = client.get("/hosts")

    assert response.status_code == 200
    assert response.json() == []


def test_get_host_by_id(client: TestClient) -> None:
    create_response = create_test_host(
        client,
        hostname="DETAIL-SERVER",
        ip_address="10.0.3.10",
    )

    host_id = create_response.json()["id"]

    response = client.get(f"/hosts/{host_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == host_id
    assert data["hostname"] == "DETAIL-SERVER"
    assert data["ip_address"] == "10.0.3.10"
    assert data["operating_system"] == "Ubuntu 24.04"
    assert data["status"] == "unknown"


def test_get_host_returns_not_found(client: TestClient) -> None:
    response = client.get("/hosts/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }


def test_update_host_partial(client: TestClient) -> None:
    create_response = create_test_host(
        client,
        hostname="UPDATE-SERVER",
        ip_address="10.0.4.10",
    )

    host_id = create_response.json()["id"]

    response = client.patch(
        f"/hosts/{host_id}",
        json={
            "ip_address": "10.0.4.20",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == host_id
    assert data["hostname"] == "UPDATE-SERVER"
    assert data["ip_address"] == "10.0.4.20"
    assert data["operating_system"] == "Ubuntu 24.04"


def test_update_host_returns_not_found(client: TestClient) -> None:
    response = client.patch(
        "/hosts/999999",
        json={
            "ip_address": "10.0.5.20",
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }


def test_update_host_duplicate_hostname_returns_conflict(
    client: TestClient,
) -> None:
    first_response = create_test_host(
        client,
        hostname="SERVER-FIRST",
        ip_address="10.0.6.10",
    )
    second_response = create_test_host(
        client,
        hostname="SERVER-SECOND",
        ip_address="10.0.6.20",
    )

    second_host_id = second_response.json()["id"]

    response = client.patch(
        f"/hosts/{second_host_id}",
        json={
            "hostname": first_response.json()["hostname"],
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "A host with this hostname already exists.",
    }


def test_delete_host(client: TestClient) -> None:
    create_response = create_test_host(
        client,
        hostname="DELETE-SERVER",
        ip_address="10.0.7.10",
    )

    host_id = create_response.json()["id"]

    delete_response = client.delete(f"/hosts/{host_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/hosts/{host_id}")

    assert get_response.status_code == 404


def test_delete_host_returns_not_found(client: TestClient) -> None:
    response = client.delete("/hosts/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Host not found.",
    }
