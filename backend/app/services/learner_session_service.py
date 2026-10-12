import hashlib
import re
import secrets

from app.db.repositories import LearnerSessionRepository

SESSION_COOKIE_NAME = "goalforge_session"
_SESSION_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{40,128}$")


class LearnerSessionError(ValueError):
    """Raised when an anonymous session is invalid."""


class LearnerSessionService:
    def __init__(self, repository: LearnerSessionRepository | None = None) -> None:
        self.repository = repository or LearnerSessionRepository()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def create_session(self) -> tuple[str, str]:
        token = secrets.token_urlsafe(32)
        learner_id = self.repository.create(self._hash_token(token))
        return token, learner_id

    def resolve(self, token: str | None) -> str:
        if not token or not _SESSION_TOKEN_PATTERN.fullmatch(token):
            raise LearnerSessionError("A valid anonymous learner session is required")
        learner_id = self.repository.get_learner_id(self._hash_token(token))
        if learner_id is None:
            raise LearnerSessionError("Anonymous learner session is invalid or expired")
        return learner_id


learner_session_service = LearnerSessionService()
