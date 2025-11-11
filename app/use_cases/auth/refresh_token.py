from typing import Any, Dict

from sqlalchemy.orm import Session

from ...services.auth_service import AuthService


class RefreshTokenUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)

    def execute(self, token: str) -> Dict[str, Any]:
        return self.auth_service.refresh_token(token)
