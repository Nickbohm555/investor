import hashlib
from dataclasses import dataclass

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer


class InvalidApprovalTokenError(ValueError):
    """Raised when an approval token cannot be validated."""


class ExpiredApprovalTokenError(InvalidApprovalTokenError):
    """Raised when an approval token has expired."""


@dataclass(frozen=True)
class ApprovalTokenPayload:
    run_id: str
    decision: str
    token_id: str


def _get_serializer(secret: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret)


def sign_approval_token(run_id: str, decision: str, secret: str, ttl_seconds: int) -> str:
    serializer = _get_serializer(secret)
    return serializer.dumps(
        {
            "run_id": run_id,
            "decision": decision,
        },
        salt="approval-token",
    )


def verify_approval_token(token: str, secret: str, ttl_seconds: int) -> ApprovalTokenPayload:
    serializer = _get_serializer(secret)
    try:
        payload = serializer.loads(token, max_age=ttl_seconds, salt="approval-token")
    except SignatureExpired as exc:
        raise ExpiredApprovalTokenError("Approval token expired") from exc
    except BadSignature as exc:
        raise InvalidApprovalTokenError("Approval token invalid") from exc
    return ApprovalTokenPayload(
        run_id=payload["run_id"],
        decision=payload["decision"],
        token_id=hashlib.sha256(token.encode("utf-8")).hexdigest(),
    )
