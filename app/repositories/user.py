from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        try:
            return (
                self.db.query(User).filter(User.username == username).first()
            )
        except SQLAlchemyError as e:
            raise e

    def get_by_email(self, email: str) -> Optional[User]:
        try:
            return self.db.query(User).filter(User.email == email).first()
        except SQLAlchemyError as e:
            raise e

    def get_by_username_or_email(
        self, username_or_email: str
    ) -> Optional[User]:
        try:
            return (
                self.db.query(User)
                .filter(
                    (User.username == username_or_email)
                    | (User.email == username_or_email)
                )
                .first()
            )
        except SQLAlchemyError as e:
            raise e

    def exists_by_username(self, username: str) -> bool:
        try:
            return (
                self.db.query(User).filter(User.username == username).first()
                is not None
            )
        except SQLAlchemyError as e:
            raise e

    def exists_by_email(self, email: str) -> bool:
        try:
            return (
                self.db.query(User).filter(User.email == email).first()
                is not None
            )
        except SQLAlchemyError as e:
            raise e

    def get_user_wishes(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        try:
            user = self.get(user_id)
            if user:
                return user.wishes[skip : skip + limit]
            return []
        except SQLAlchemyError as e:
            raise e
