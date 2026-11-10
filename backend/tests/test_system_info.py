"""
Test for GET /api/system/info endpoint
"""
from fastapi import status


def test_system_info_endpoint(client):
    response = client.get("/api/system/info")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["application_name"] == "Cyber Raksha AI"
    assert "version" in data
    assert "Stage 1" in data["development_stage"]
    assert data["backend_status"] == "OPERATIONAL"
    assert "database_status" in data
    assert data["database_status"]["connected"] is True
    assert "implemented_components" in data
    assert isinstance(data["implemented_components"], list)
    assert len(data["implemented_components"]) > 0
    assert "planned_components" in data
    assert isinstance(data["planned_components"], list)
    assert len(data["planned_components"]) > 0


def test_modules_endpoint(client):
    response = client.get("/api/modules")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_modules"] == 6
    assert data["implemented_count"] >= 0
    assert data["planned_count"] <= 6
    module_names = [m["name"] for m in data["modules"]]
    assert "Phishing Detection" in module_names
    assert "Malicious URL Detection" in module_names
    assert "Voice Cloning Detection" in module_names
    assert "Communication Risk Analysis" in module_names
    assert "Threat Intelligence" in module_names
    assert "Risk Assessment Engine" in module_names
