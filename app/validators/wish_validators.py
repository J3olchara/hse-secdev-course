from typing import Optional

from ..core.exceptions import ValidationError


class WishValidators:
    @staticmethod
    def validate_title(title: str) -> None:
        if not title:
            raise ValidationError("Title is required")

        if len(title) < 1:
            raise ValidationError("Title cannot be empty")

        if len(title) > 200:
            raise ValidationError(
                "Title must be no more than 200 characters long"
            )

    @staticmethod
    def validate_description(description: Optional[str]) -> None:
        if description is not None:
            if len(description) > 1000:
                raise ValidationError(
                    "Description must be no more than 1000 characters long"
                )

    @staticmethod
    def validate_wish_id(wish_id: int) -> None:
        if not isinstance(wish_id, int):
            raise ValidationError("Wish ID must be an integer")

        if wish_id <= 0:
            raise ValidationError("Wish ID must be a positive integer")

    @staticmethod
    def validate_pagination_params(skip: int, limit: int) -> None:
        if not isinstance(skip, int) or skip < 0:
            raise ValidationError("Skip must be a non-negative integer")

        if not isinstance(limit, int) or limit <= 0:
            raise ValidationError("Limit must be a positive integer")

        if limit > 100:
            raise ValidationError("Limit cannot exceed 100")
