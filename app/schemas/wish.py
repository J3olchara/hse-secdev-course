from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WishBase(BaseModel):
    title: str = Field(
        ..., min_length=1, max_length=200, description="Wish title"
    )
    description: Optional[str] = Field(
        None, max_length=5000, description="Wish description"
    )

    @field_validator('title', 'description')
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        """Защита от XSS атак (ADR-004, R7)"""
        if v is None:
            return v

        # Проверка на потенциально опасный контент
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        v_lower = v.lower()

        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(
                    f'HTML/JS content not allowed in {cls.__name__}'
                )

        return v.strip()


class WishCreate(WishBase):
    pass


class WishUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)

    @field_validator('title', 'description')
    @classmethod
    def sanitize_html(cls, v: str | None) -> str | None:
        """Защита от XSS атак (ADR-004)"""
        if v is None:
            return v

        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        v_lower = v.lower()

        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError('HTML/JS content not allowed')

        return v.strip()


class WishResponse(WishBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WishListResponse(BaseModel):
    wishes: list[WishResponse]
    total: int
    page: int
    size: int
