# services/orchestrator/tests/test_health.py
from fastapi.testclient import TestClient
from services.orchestrator.app.main import app

def test_health_endpoint_returns_ok():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert "timestamp" in body
