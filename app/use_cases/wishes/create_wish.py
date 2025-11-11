from sqlalchemy.orm import Session

from ...schemas.wish import WishCreate, WishResponse
from ...services.wish_service import WishService


class CreateWishUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.wish_service = WishService(db)

    def execute(self, user_id: int, wish_data: WishCreate) -> WishResponse:
        return self.wish_service.create_wish(user_id, wish_data)
