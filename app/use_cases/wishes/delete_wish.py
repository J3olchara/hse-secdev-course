from sqlalchemy.orm import Session

from ...services.wish_service import WishService


class DeleteWishUseCase:
    def __init__(self, db: Session):
        self.db = db
        self.wish_service = WishService(db)

    def execute(self, user_id: int, wish_id: int) -> bool:
        return self.wish_service.delete_wish(user_id, wish_id)
