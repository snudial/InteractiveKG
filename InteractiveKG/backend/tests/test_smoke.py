"""Smoke tests: the app must import, register its routes, and serve endpoints
that do not touch Neo4j, even when no database or KGOT checkout is available.

Run from the backend directory: python -m pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    # TestClient runs the lifespan handler; a failed Neo4j connection is logged
    # but must not prevent startup.
    with TestClient(app) as test_client:
        yield test_client


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_expected_routers_registered(client):
    paths = set(client.get("/openapi.json").json()["paths"])
    expected = {
        "/api/graph/data",
        "/api/graph/nodes",
        "/api/graph/relationships",
        "/api/graph/hierarchical-analysis",
        "/api/graph/community-detail",
        "/api/graph/explain-node",
        "/api/kgot/enhanced-solve",
        "/api/kgot/pure-internal-retrieve",
        "/api/kgot/load-error-data",
        "/api/chatbot/create-session",
        "/api/chatbot/chat",
        "/api/chatbot/load-scenario",
    }
    missing = expected - paths
    assert not missing, f"Routes missing from the app: {sorted(missing)}"


def test_kgot_status_degrades_gracefully(client):
    """/api/kgot/status must answer even when the LLM/KGOT stack is absent."""
    response = client.get("/api/kgot/status")
    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"available", "llm_enabled", "features", "message"}


def test_openapi_schema_builds(client):
    """Pydantic models must all be schema-compatible."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert len(response.json()["paths"]) > 30
