from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ....core.exceptions import NotFoundError
from ....schemas.wish import (
    WishCreate,
    WishListResponse,
    WishResponse,
    WishUpdate,
)
from ....services.wish_service import WishService
from ....use_cases.wishes import (
    CreateWishUseCase,
    DeleteWishUseCase,
    GetWishUseCase,
    UpdateWishUseCase,
)
from ...dependencies.auth import get_current_user_id
from ...dependencies.database import get_database

router = APIRouter(prefix="/wishes", tags=["wishes"])


@router.post("", response_model=WishResponse)
async def create_wish(
    wish_data: WishCreate,
    db: Session = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        use_case = CreateWishUseCase(db)
        return use_case.execute(current_user_id, wish_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/{wish_id}", response_model=WishResponse)
async def get_wish(
    wish_id: int,
    db: Session = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        use_case = GetWishUseCase(db)
        return use_case.execute(current_user_id, wish_id)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("", response_model=WishListResponse)
async def get_wishes(
    skip: int = Query(
        0,
        ge=0,
        le=10000,
        description="Number of wishes to skip (max 10000 для защиты от DoS, ADR-005)",
    ),
    limit: int = Query(
        10,
        ge=1,
        le=50,
        description="Number of wishes to return (max 50 для защиты от DoS, ADR-005)",
    ),
    search: Optional[str] = Query(
        None,
        max_length=100,
        description="Search wishes by title (max 100 символов)",
    ),
    db: Session = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Получение списка желаний с защитой от DoS атак (NFR-06, STRIDE D).

    Ограничения для предотвращения DoS:
    - skip <= 10000 (ограничение offset)
    - limit <= 50 (ограничение размера ответа)
    - search <= 100 символов
    """
    try:
        wish_service = WishService(db)

        if search:
            return wish_service.search_wishes(
                current_user_id, search, skip, limit
            )
        else:
            return wish_service.get_user_wishes(current_user_id, skip, limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.patch("/{wish_id}", response_model=WishResponse)
async def update_wish(
    wish_id: int,
    wish_data: WishUpdate,
    db: Session = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        use_case = UpdateWishUseCase(db)
        return use_case.execute(current_user_id, wish_id, wish_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/{wish_id}")
async def delete_wish(
    wish_id: int,
    db: Session = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        use_case = DeleteWishUseCase(db)
        success = use_case.execute(current_user_id, wish_id)
        if success:
            return {"message": "Wish deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete wish",
            )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
