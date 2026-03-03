import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuthorityVerify:
    def test_low_risk_action_is_authorized(self):
        response = client.post("/authority/verify", json={"action": "READ_FILE"})
        assert response.status_code == 200
        assert response.json()["authorized"] is True

    def test_protected_action_without_token_is_denied(self):
        response = client.post("/authority/verify", json={"action": "FILE_DELETE"})
        assert response.status_code == 200
        assert response.json()["authorized"] is False

    def test_protected_action_with_correct_token_is_authorized(self):
        with patch.dict(os.environ, {"ROOTAI_AUTH_TOKEN": "s3cr3t"}):
            response = client.post(
                "/authority/verify", json={"action": "FILE_DELETE", "token": "s3cr3t"}
            )
        assert response.status_code == 200
        assert response.json()["authorized"] is True

    def test_response_includes_action_field(self):
        response = client.post("/authority/verify", json={"action": "LOG_EVENT"})
        assert response.json()["action"] == "LOG_EVENT"


class TestPipelineExecute:
    def test_pipeline_returns_expected_keys(self):
        response = client.post("/pipeline/execute", json={"query": "Create an auth session"})
        assert response.status_code == 200
        body = response.json()
        for key in ("intent", "semantic_roots", "hard_constraints", "reliability", "hallucination_risk"):
            assert key in body

    def test_pipeline_echoes_query_as_intent(self):
        response = client.post("/pipeline/execute", json={"query": "validate input"})
        assert response.json()["intent"] == "validate input"

    def test_pipeline_returns_hard_constraints_from_yaml(self):
        response = client.post("/pipeline/execute", json={"query": "test query"})
        constraints = response.json()["hard_constraints"]
        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_pipeline_missing_worm_file_returns_404(self):
        response = client.post(
            "/pipeline/execute",
            json={"query": "test", "worm_path": "nonexistent/path.yaml"},
        )
        assert response.status_code == 404
