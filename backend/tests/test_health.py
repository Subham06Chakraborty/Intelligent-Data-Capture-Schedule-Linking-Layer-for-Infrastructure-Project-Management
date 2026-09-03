"""
tests/test_health.py
---------------------
Basic smoke test for the health endpoint.

Run with:
    pytest
(from inside the backend/ folder, with the venv activated)
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "service" in body


def test_root_endpoint_returns_200():
    response = client.get("/")
    assert response.status_code == 200
