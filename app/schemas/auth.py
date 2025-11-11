from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 30


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[datetime] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    token: str
