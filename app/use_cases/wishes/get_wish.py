from sqlalchemy.orm import Session

from ...schemas.wish import WishResponse
from ...services.wish_service import WishService


class GetWishUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.wish_service = WishService(db)

    def execute(self, user_id: int, wish_id: int) -> WishResponse:
        return self.wish_service.get_wish(user_id, wish_id)
