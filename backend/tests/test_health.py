def test_health_returns_200_when_all_dependencies_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}


def test_health_returns_503_when_redis_down(client, monkeypatch):
    monkeypatch.setattr("app.api.health._check_redis", lambda: False)

    response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["redis"] == "error"
    assert body["database"] == "ok"


def test_health_returns_503_when_database_down(client, monkeypatch):
    monkeypatch.setattr("app.api.health._check_database", lambda db: False)

    response = client.get("/health")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["database"] == "error"
    assert body["redis"] == "ok"
