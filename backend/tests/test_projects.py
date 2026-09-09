from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_project_validation():
    response = client.post(
        "/api/projects",
        json={"name": "X", "start_date": "2026-10-01", "finish_date": "2026-09-01"},
    )
    assert response.status_code == 422


def test_project_list_uses_service():
    with patch("app.routes.projects.project_service.list_projects", return_value=[]):
        response = client.get("/api/projects")
    assert response.status_code == 200
    assert response.json() == []
