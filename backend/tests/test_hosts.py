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
