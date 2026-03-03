import os
import pytest
from unittest.mock import patch

from authority_gate import AuthorityGate


@pytest.fixture
def gate_with_token():
    with patch.dict(os.environ, {"ROOTAI_AUTH_TOKEN": "secret-token"}):
        yield AuthorityGate()


@pytest.fixture
def gate_no_token():
    env = os.environ.copy()
    env.pop("ROOTAI_AUTH_TOKEN", None)
    with patch.dict(os.environ, env, clear=True):
        yield AuthorityGate()


class TestVerifyAuthority:
    def test_low_risk_action_bypasses_gate(self, gate_with_token):
        assert gate_with_token.verify_authority("READ_FILE", None) is True

    def test_protected_action_with_correct_token(self, gate_with_token):
        assert gate_with_token.verify_authority("FILE_DELETE", "secret-token") is True

    def test_protected_action_with_wrong_token(self, gate_with_token):
        assert gate_with_token.verify_authority("FILE_DELETE", "wrong-token") is False

    def test_protected_action_with_no_token(self, gate_with_token):
        assert gate_with_token.verify_authority("FILE_DELETE", None) is False

    def test_protected_action_when_governance_token_missing(self, gate_no_token):
        assert gate_no_token.verify_authority("FILE_DELETE", "any-token") is False

    def test_all_protected_actions_require_auth(self, gate_with_token):
        for action in ["FILE_DELETE", "NETWORK_EXFIL", "SYS_WRITE"]:
            assert gate_with_token.verify_authority(action, "wrong") is False
            assert gate_with_token.verify_authority(action, "secret-token") is True


class TestInterceptExecution:
    def test_plan_with_no_protected_actions(self, gate_with_token):
        plan = [{"action": "LOG_EVENT", "target": "/var/log/app.log"}]
        result = gate_with_token.intercept_execution(plan)
        assert result["status"] == "200_OK"

    def test_plan_blocked_without_token(self, gate_with_token):
        plan = [{"action": "FILE_DELETE", "target": "/root/secure_configs"}]
        result = gate_with_token.intercept_execution(plan)
        assert result["status"] == "401_UNAUTHORIZED"
        assert "FILE_DELETE" in result["error"]

    def test_plan_approved_with_correct_token(self, gate_with_token):
        plan = [{"action": "FILE_DELETE", "target": "/root/secure_configs", "token": "secret-token"}]
        result = gate_with_token.intercept_execution(plan)
        assert result["status"] == "200_OK"

    def test_plan_blocked_at_first_unauthorized_step(self, gate_with_token):
        plan = [
            {"action": "FILE_DELETE", "target": "/root/secure_configs"},
            {"action": "SYS_WRITE", "target": "/etc/hosts", "token": "secret-token"},
        ]
        result = gate_with_token.intercept_execution(plan)
        assert result["status"] == "401_UNAUTHORIZED"
        assert "FILE_DELETE" in result["error"]

    def test_empty_plan_is_approved(self, gate_with_token):
        result = gate_with_token.intercept_execution([])
        assert result["status"] == "200_OK"

    def test_mixed_plan_all_authorized(self, gate_with_token):
        plan = [
            {"action": "LOG_EVENT"},
            {"action": "FILE_DELETE", "token": "secret-token"},
            {"action": "SYS_WRITE", "token": "secret-token"},
        ]
        result = gate_with_token.intercept_execution(plan)
        assert result["status"] == "200_OK"
