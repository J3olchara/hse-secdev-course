from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class Token(BaseModel):
    model_config = ConfigDict(extra='forbid')

    access_token: str
    token_type: str = "bearer"
    expires_in: int = 30


class TokenData(BaseModel):
    model_config = ConfigDict(extra='forbid')

    username: Optional[str] = None
    user_id: Optional[int] = None
    exp: Optional[datetime] = None


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    refresh_token: str


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')

    token: str
