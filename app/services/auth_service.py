from sqlalchemy.orm import Session

from ..core.auth import create_access_token, verify_password
from ..core.exceptions import NotFoundError, UnauthorizedError
from ..repositories.user import UserRepository
from ..schemas.user import UserLogin


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def login_user(self, login_data: UserLogin) -> dict:
        user = self.user_repo.get_by_username_or_email(login_data.username)
        if not user:
            raise UnauthorizedError("Invalid username or password")

        if not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedError("Invalid username or password")

        token_data = {"sub": str(user.id), "username": user.username}
        access_token = create_access_token(token_data)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at,
            },
            "access_token": access_token,
            "token_type": "bearer",
        }

    def get_current_user(self, token: str) -> dict:
        from ..core.auth import verify_token

        payload = verify_token(token)
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise UnauthorizedError("Invalid token")

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError):
            raise UnauthorizedError("Invalid user ID in token")

        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "created_at": user.created_at,
        }

    def refresh_token(self, token: str) -> dict:
        user_data = self.get_current_user(token)

        token_data = {
            "sub": str(user_data["id"]),
            "username": user_data["username"],
        }
        access_token = create_access_token(token_data)

        return {"access_token": access_token, "token_type": "bearer"}
