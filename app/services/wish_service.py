from sqlalchemy.orm import Session

from ..core.exceptions import NotFoundError
from ..repositories.user import UserRepository
from ..repositories.wish import WishRepository
from ..schemas.wish import (
    WishCreate,
    WishListResponse,
    WishResponse,
    WishUpdate,
)


class WishService:
    def __init__(self, db: Session):
        self.db = db
        self.wish_repo = WishRepository(db)
        self.user_repo = UserRepository(db)

    def create_wish(self, user_id: int, wish_data: WishCreate) -> WishResponse:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        wish_dict = {
            "title": wish_data.title,
            "description": wish_data.description,
            "user_id": user_id,
        }

        wish = self.wish_repo.create(wish_dict)

        return WishResponse(
            id=wish.id,
            title=wish.title,
            description=wish.description,
            user_id=wish.user_id,
            created_at=wish.created_at,
            updated_at=wish.updated_at,
        )

    def get_wish(self, user_id: int, wish_id: int) -> WishResponse:
        wish = self.wish_repo.get_by_user_and_id(user_id, wish_id)
        if not wish:
            raise NotFoundError("Wish not found")

        return WishResponse(
            id=wish.id,
            title=wish.title,
            description=wish.description,
            user_id=wish.user_id,
            created_at=wish.created_at,
            updated_at=wish.updated_at,
        )

    def get_user_wishes(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> WishListResponse:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        wishes = self.wish_repo.get_by_user_id(user_id, skip, limit)
        total = self.wish_repo.count_by_user_id(user_id)

        wish_responses = [
            WishResponse(
                id=wish.id,
                title=wish.title,
                description=wish.description,
                user_id=wish.user_id,
                created_at=wish.created_at,
                updated_at=wish.updated_at,
            )
            for wish in wishes
        ]

        return WishListResponse(
            wishes=wish_responses, total=total, page=skip // limit, size=limit
        )

    def update_wish(
        self, user_id: int, wish_id: int, wish_data: WishUpdate
    ) -> WishResponse:
        wish = self.wish_repo.get_by_user_and_id(user_id, wish_id)
        if not wish:
            raise NotFoundError("Wish not found")

        update_data = {}
        if wish_data.title is not None:
            update_data["title"] = wish_data.title
        if wish_data.description is not None:
            update_data["description"] = wish_data.description

        updated_wish = self.wish_repo.update(wish, update_data)

        return WishResponse(
            id=updated_wish.id,
            title=updated_wish.title,
            description=updated_wish.description,
            user_id=updated_wish.user_id,
            created_at=updated_wish.created_at,
            updated_at=updated_wish.updated_at,
        )

    def delete_wish(self, user_id: int, wish_id: int) -> bool:
        wish = self.wish_repo.get_by_user_and_id(user_id, wish_id)
        if not wish:
            raise NotFoundError("Wish not found")

        return self.wish_repo.delete_by_user_and_id(user_id, wish_id)

    def search_wishes(
        self, user_id: int, title: str, skip: int = 0, limit: int = 100
    ) -> WishListResponse:
        user = self.user_repo.get(user_id)
        if not user:
            raise NotFoundError("User not found")

        wishes = self.wish_repo.search_by_title(user_id, title, skip, limit)
        total = len(wishes)

        wish_responses = [
            WishResponse(
                id=wish.id,
                title=wish.title,
                description=wish.description,
                user_id=wish.user_id,
                created_at=wish.created_at,
                updated_at=wish.updated_at,
            )
            for wish in wishes
        ]

        return WishListResponse(
            wishes=wish_responses, total=total, page=skip // limit, size=limit
        )
