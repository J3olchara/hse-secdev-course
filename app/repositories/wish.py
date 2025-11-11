from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models.wish import Wish
from .base import BaseRepository


class WishRepository(BaseRepository[Wish]):
    def __init__(self, db: Session):
        super().__init__(Wish, db)

    def get_by_user_id(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Wish]:
        try:
            return (
                self.db.query(Wish)
                .filter(Wish.user_id == user_id)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def get_by_user_and_id(self, user_id: int, wish_id: int) -> Optional[Wish]:
        try:
            return (
                self.db.query(Wish)
                .filter(Wish.id == wish_id, Wish.user_id == user_id)
                .first()
            )
        except SQLAlchemyError as e:
            raise e

    def count_by_user_id(self, user_id: int) -> int:
        try:
            return self.db.query(Wish).filter(Wish.user_id == user_id).count()
        except SQLAlchemyError as e:
            raise e

    def search_by_title(
        self, user_id: int, title: str, skip: int = 0, limit: int = 100
    ) -> List[Wish]:
        try:
            return (
                self.db.query(Wish)
                .filter(
                    Wish.user_id == user_id, Wish.title.ilike(f"%{title}%")
                )
                .offset(skip)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise e

    def get_user_wishes(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Wish]:
        return self.get_by_user_id(user_id, skip, limit)

    def search_wishes(
        self, user_id: int, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[Wish]:
        return self.search_by_title(user_id, search_term, skip, limit)

    def delete_by_user_and_id(self, user_id: int, wish_id: int) -> bool:
        try:
            wish = self.get_by_user_and_id(user_id, wish_id)
            if wish:
                self.db.delete(wish)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
