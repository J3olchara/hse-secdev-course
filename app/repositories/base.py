from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def create(self, obj_in: Dict[str, Any]) -> ModelType:
        try:
            if hasattr(obj_in, '__dict__'):
                obj_data = {
                    k: v
                    for k, v in obj_in.__dict__.items()
                    if not k.startswith('_')
                }
            else:
                obj_data = obj_in

            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def get(self, id: int) -> Optional[ModelType]:
        try:
            return (
                self.db.query(self.model).filter(self.model.id == id).first()
            )
        except SQLAlchemyError as e:
            raise e

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        try:
            return self.db.query(self.model).offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            raise e

    def update(self, db_obj: ModelType, obj_in: Dict[str, Any]) -> ModelType:
        try:
            if hasattr(obj_in, '__dict__'):
                update_data = {
                    k: v
                    for k, v in obj_in.__dict__.items()
                    if not k.startswith('_') and v is not None
                }
            else:
                update_data = obj_in

            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def delete(self, id: int) -> bool:
        try:
            obj = self.db.query(self.model).filter(self.model.id == id).first()
            if obj:
                self.db.delete(obj)
                self.db.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e

    def count(self) -> int:
        try:
            return self.db.query(self.model).count()
        except SQLAlchemyError as e:
            raise e
