from sqlalchemy.orm import Session

from ...schemas.wish import WishResponse, WishUpdate
from ...services.wish_service import WishService


class UpdateWishUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.wish_service = WishService(db)

    def execute(
        self, user_id: int, wish_id: int, wish_data: WishUpdate
    ) -> WishResponse:
        return self.wish_service.update_wish(user_id, wish_id, wish_data)
