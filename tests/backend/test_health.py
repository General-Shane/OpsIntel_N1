import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/system/status")
    assert response.status_code == 200
    assert response.json() == {"status": "HEALTHY", "message": "OPSINTEL API is running."}

def test_root_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "HEALTHY"}
