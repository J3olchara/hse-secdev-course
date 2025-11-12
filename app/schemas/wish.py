from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WishBase(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(
        ..., min_length=1, max_length=200, description="Wish title"
    )
    description: Optional[str] = Field(
        None, max_length=5000, description="Wish description"
    )
    price: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Wish price (безопасная работа с деньгами, ADR-005)",
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
    model_config = ConfigDict(extra='forbid')

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    price: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=12,
        decimal_places=2,
        description="Wish price",
    )

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

    model_config = ConfigDict(from_attributes=True, extra='forbid')

    @field_validator('created_at', 'updated_at', mode='before')
    @classmethod
    def normalize_datetime(cls, v: datetime) -> datetime:
        """Нормализация datetime в UTC (ADR-005, NFR-08)"""
        if v is None:
            return v
        if isinstance(v, datetime):
            if v.tzinfo is None:
                # Если naive datetime, считаем его UTC
                return v.replace(tzinfo=timezone.utc)
            # Конвертируем в UTC
            return v.astimezone(timezone.utc)
        return v


class WishListResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')

    wishes: list[WishResponse]
    total: int
    page: int
    size: int
