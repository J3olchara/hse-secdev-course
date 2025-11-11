from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from ...core.exceptions import UnauthorizedError
from ...services.auth_service import AuthService
from ..dependencies.database import get_database

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database),
) -> dict:
    try:
        token = credentials.credentials
        auth_service = AuthService(db)
        return auth_service.get_current_user(token)
    except UnauthorizedError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> int:
    return current_user["id"]


def require_auth(current_user: dict = Depends(get_current_user)) -> dict:
    return current_user
