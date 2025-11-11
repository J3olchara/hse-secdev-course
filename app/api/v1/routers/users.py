from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ....core.exceptions import ConflictError, NotFoundError
from ....schemas.user import UserResponse, UserUpdate
from ....services.user_service import UserService
from ...dependencies.auth import get_current_user, get_current_user_id
from ...dependencies.database import get_database

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        created_at=current_user["created_at"],
    )


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    db: Session = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        user_service = UserService(db)
        return user_service.update_user(current_user_id, user_data)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.delete("/me")
async def delete_my_account(
    db: Session = Depends(get_database),
    current_user_id: int = Depends(get_current_user_id),
):
    try:
        user_service = UserService(db)
        success = user_service.delete_user(current_user_id)
        if success:
            return {"message": "Account deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete account",
            )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
