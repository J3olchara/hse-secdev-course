import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserBase(BaseModel):
    username: str = Field(
        ..., min_length=3, max_length=50, description="Username"
    )
    email: EmailStr = Field(..., max_length=100, description="Email address")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Валидация username - только буквы, цифры, дефис, underscore (ADR-004)"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'Username must contain only letters, numbers, dashes and underscores'
            )
        return v


class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        """Валидация username (ADR-004)"""
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError(
                'Username must contain only letters, numbers, dashes and underscores'
            )
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Валидация пароля - минимум 1 буква и 1 цифра (ADR-004, NFR-01)"""
        if v is None:
            return v
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v
