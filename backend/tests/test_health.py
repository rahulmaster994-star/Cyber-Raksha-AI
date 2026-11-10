"""
Test for GET /api/health endpoint
"""
from fastapi import status


def test_health_check_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["application"] == "Cyber Raksha AI"
    assert "version" in data
    assert isinstance(data["database_connected"], bool)
    assert data["database_connected"] is True
    assert isinstance(data["database_latency_ms"], (int, float))
    assert data["database_latency_ms"] >= 0
    assert "uptime_seconds" in data
    assert "timestamp" in data


def test_health_check_v1_alias(client):
    response = client.get("/api/v1/health")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["database_connected"] is True
