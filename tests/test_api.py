"""
Test suite for API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from api import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAPIEndpoints:
    """Tests for FastAPI endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data

    def test_process_classification(self, client):
        """Test classification task processing."""
        response = client.post(
            "/process",
            json={
                "task_type": "classification",
                "input_data": "def hello(): pass",
                "parameters": {},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "result" in data

    def test_process_generation(self, client):
        """Test generation task processing."""
        response = client.post(
            "/process",
            json={
                "task_type": "generation",
                "input_data": "create a hello world function",
                "parameters": {"language": "python"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_process_invalid_task_type(self, client):
        """Test processing with invalid task type."""
        response = client.post(
            "/process", json={"task_type": "invalid", "input_data": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False

    def test_auto_route(self, client):
        """Test auto-routing endpoint."""
        response = client.post(
            "/auto-route",
            json={
                "input_data": "def hello(): pass",
                "description": "generate documentation",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "agents" in data

    def test_get_all_agents(self, client):
        """Test getting all agents info."""
        response = client.get("/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 4

    def test_get_specific_agent(self, client):
        """Test getting specific agent info."""
        response = client.get("/agents/classification")
        assert response.status_code == 200
        data = response.json()
        assert "agent_type" in data

    def test_get_invalid_agent(self, client):
        """Test getting invalid agent info."""
        response = client.get("/agents/invalid")
        assert response.status_code == 404

    def test_get_task_types(self, client):
        """Test getting task types."""
        response = client.get("/task-types")
        assert response.status_code == 200
        data = response.json()
        assert "task_types" in data
        assert len(data["task_types"]) == 4
