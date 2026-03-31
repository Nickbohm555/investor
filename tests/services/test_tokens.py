import time

import pytest

from app.config import Settings
from app.services.tokens import ExpiredApprovalTokenError, sign_approval_token, verify_approval_token


@pytest.fixture
def settings() -> Settings:
    return Settings(app_secret="test-secret")


def test_sign_and_verify_token_round_trip(settings: Settings):
    token = sign_approval_token(
        run_id="run-123",
        decision="approve",
        secret=settings.app_secret,
        ttl_seconds=900,
    )

    payload = verify_approval_token(token, secret=settings.app_secret, ttl_seconds=900)

    assert payload.run_id == "run-123"
    assert payload.decision == "approve"
    assert payload.token_id


def test_verify_token_rejects_expired_token(settings: Settings):
    token = sign_approval_token(
        run_id="run-123",
        decision="reject",
        secret=settings.app_secret,
        ttl_seconds=1,
    )

    time.sleep(2.1)

    with pytest.raises(ExpiredApprovalTokenError):
        verify_approval_token(token, secret=settings.app_secret, ttl_seconds=1)
