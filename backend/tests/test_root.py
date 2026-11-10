"""
Test for GET / endpoint
"""
from fastapi import status


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "name" in data
    assert data["name"] == "Cyber Raksha AI"
    assert "version" in data
    assert data["status"] == "OPERATIONAL"
    assert "Stage 1" in data["stage"]
