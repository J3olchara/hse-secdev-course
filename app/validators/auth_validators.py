import re

from ..core.exceptions import ValidationError


class AuthValidators:
    @staticmethod
    def validate_username(username: str) -> None:
        if not username:
            raise ValidationError("Username is required")

        if len(username) < 3:
            raise ValidationError(
                "Username must be at least 3 characters long"
            )

        if len(username) > 50:
            raise ValidationError(
                "Username must be no more than 50 characters long"
            )

        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            raise ValidationError(
                "Username can only contain letters, numbers, and underscores"
            )

    @staticmethod
    def validate_email(email: str) -> None:
        if not email:
            raise ValidationError("Email is required")

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValidationError("Invalid email format")

        if len(email) > 100:
            raise ValidationError(
                "Email must be no more than 100 characters long"
            )

    @staticmethod
    def validate_password(password: str) -> None:
        if not password:
            raise ValidationError("Password is required")

        if len(password) < 6:
            raise ValidationError(
                "Password must be at least 6 characters long"
            )

        if len(password) > 128:
            raise ValidationError(
                "Password must be no more than 128 characters long"
            )

    @staticmethod
    def validate_token(token: str) -> None:
        if not token:
            raise ValidationError("Token is required")

        if not token.startswith("Bearer "):
            raise ValidationError("Token must start with 'Bearer '")

        if len(token) < 10:
            raise ValidationError("Invalid token format")
