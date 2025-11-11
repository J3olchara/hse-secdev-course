from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ....core.exceptions import UnauthorizedError
from ....schemas.auth import LogoutRequest, RefreshTokenRequest, Token
from ....schemas.user import UserLogin
from ....use_cases.auth import LoginUserUseCase, RefreshTokenUseCase
from ...dependencies.auth import get_current_user
from ...dependencies.database import get_database

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_database),
):
    try:
        use_case = LoginUserUseCase(db)
        result = use_case.execute(login_data)
        return Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=30,
        )
    except UnauthorizedError as e:
        # Middleware уже отслеживает все попытки входа
        raise UnauthorizedError(str(e))


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: Session = Depends(get_database)
):
    try:
        use_case = RefreshTokenUseCase(db)
        result = use_case.execute(refresh_data.refresh_token)
        return Token(
            access_token=result["access_token"],
            token_type=result["token_type"],
            expires_in=30,
        )
    except UnauthorizedError:
        raise


@router.post("/logout")
async def logout(
    logout_data: LogoutRequest, current_user: dict = Depends(get_current_user)
):
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
):
    return current_user
