from sqlalchemy.orm import Session

from ..core.exceptions import ConflictError, NotFoundError
from ..repositories.user import UserRepository
from ..schemas.user import UserResponse, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def get_user_by_id(self, user_id: int) -> UserResponse:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
        )

    def get_user_by_username(self, username: str) -> UserResponse:
        user = self.user_repo.get_by_username(username)
        if not user:
            raise NotFoundError("User not found")

        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            created_at=user.created_at,
        )

    def update_user(self, user_id: int, user_data: UserUpdate) -> UserResponse:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        if user_data.username and user_data.username != user.username:
            if self.user_repo.exists_by_username(user_data.username):
                raise ConflictError("Username already exists")

        if user_data.email and user_data.email != user.email:
            if self.user_repo.exists_by_email(user_data.email):
                raise ConflictError("Email already exists")

        update_data = {}
        if user_data.username is not None:
            update_data["username"] = user_data.username
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.password is not None:
            from ..core.auth import hash_password

            update_data["hashed_password"] = hash_password(user_data.password)

        updated_user = self.user_repo.update(user, update_data)

        return UserResponse(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            created_at=updated_user.created_at,
        )

    def delete_user(self, user_id: int) -> bool:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        return self.user_repo.delete(user_id)

    def get_user_profile(self, user_id: int) -> UserResponse:
        return self.get_user_by_id(user_id)

    def get_user_wishes_count(self, user_id: int) -> int:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        return len(user.wishes)
