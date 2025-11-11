from typing import Any, Dict

from sqlalchemy.orm import Session

from ...schemas.user import UserLogin
from ...services.auth_service import AuthService


class LoginUserUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthService(db)

    def execute(self, login_data: UserLogin) -> Dict[str, Any]:
        return self.auth_service.login_user(login_data)
