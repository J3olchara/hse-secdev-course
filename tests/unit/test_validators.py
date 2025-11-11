"""
Unit тесты для валидаторов.
"""

import pytest

from app.core.exceptions import ValidationError
from app.validators.auth_validators import AuthValidators
from app.validators.wish_validators import WishValidators


class TestAuthValidators:
    """Тесты для AuthValidators."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.validator = AuthValidators()

    def test_validate_username_success(self):
        """Тест успешной валидации имени пользователя."""
        # Act
        self.validator.validate_username("testuser123")

        # Assert - если не выброшено исключение, тест прошел

    def test_validate_username_empty(self):
        """Тест валидации с пустым именем пользователя."""
        # Act & Assert
        with pytest.raises(ValidationError, match="Username is required"):
            self.validator.validate_username("")

    def test_validate_username_short(self):
        """Тест валидации с коротким именем пользователя."""
        # Act & Assert
        with pytest.raises(
            ValidationError,
            match="Username must be at least 3 characters long",
        ):
            self.validator.validate_username("ab")

    def test_validate_password_success(self):
        """Тест успешной валидации пароля."""
        # Act
        self.validator.validate_password("password123")

        # Assert - если не выброшено исключение, тест прошел

    def test_validate_password_short(self):
        """Тест валидации с коротким паролем."""
        # Act & Assert
        with pytest.raises(
            ValidationError,
            match="Password must be at least 6 characters long",
        ):
            self.validator.validate_password("123")

    def test_validate_username_invalid_characters(self):
        """Тест валидации имени пользователя с недопустимыми символами."""
        # Act & Assert
        expected_msg = (
            "Username can only contain letters, numbers, and underscores"
        )
        with pytest.raises(ValidationError, match=expected_msg):
            self.validator.validate_username("test@user!")

    def test_validate_username_too_long(self):
        """Тест валидации слишком длинного имени пользователя."""
        # Act & Assert
        with pytest.raises(
            ValidationError,
            match="Username must be no more than 50 characters long",
        ):
            self.validator.validate_username("a" * 51)


class TestWishValidators:
    """Тесты для WishValidators."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.validator = WishValidators()

    def test_validate_title_success(self):
        """Тест успешной валидации заголовка."""
        # Act
        self.validator.validate_title("Test Wish")

        # Assert - если не выброшено исключение, тест прошел

    def test_validate_title_empty(self):
        """Тест валидации с пустым заголовком."""
        # Act & Assert
        with pytest.raises(ValidationError, match="Title is required"):
            self.validator.validate_title("")

    def test_validate_title_too_long(self):
        """Тест валидации с слишком длинным заголовком."""
        # Act & Assert
        with pytest.raises(
            ValidationError,
            match="Title must be no more than 200 characters long",
        ):
            self.validator.validate_title("a" * 201)

    def test_validate_description_success(self):
        """Тест успешной валидации описания."""
        # Act
        self.validator.validate_description("Test Description")

        # Assert - если не выброшено исключение, тест прошел

    def test_validate_description_too_long(self):
        """Тест валидации с слишком длинным описанием."""
        # Act & Assert
        with pytest.raises(
            ValidationError,
            match="Description must be no more than 1000 characters long",
        ):
            self.validator.validate_description("a" * 1001)

    def test_validate_wish_id_success(self):
        """Тест успешной валидации ID желания."""
        # Act
        self.validator.validate_wish_id(1)

        # Assert - если не выброшено исключение, тест прошел

    def test_validate_wish_id_invalid(self):
        """Тест валидации с невалидным ID желания."""
        # Act & Assert
        with pytest.raises(
            ValidationError, match="Wish ID must be an integer"
        ):
            self.validator.validate_wish_id("invalid")

    def test_validate_wish_id_negative(self):
        """Тест валидации с отрицательным ID желания."""
        # Act & Assert
        with pytest.raises(
            ValidationError, match="Wish ID must be a positive integer"
        ):
            self.validator.validate_wish_id(-1)

    def test_validate_pagination_params_success(self):
        """Тест успешной валидации параметров пагинации."""
        # Act
        self.validator.validate_pagination_params(0, 10)

        # Assert - если не выброшено исключение, тест прошел

    def test_validate_pagination_params_invalid_skip(self):
        """Тест валидации с невалидным параметром skip."""
        # Act & Assert
        with pytest.raises(
            ValidationError, match="Skip must be a non-negative integer"
        ):
            self.validator.validate_pagination_params(-1, 10)

    def test_validate_pagination_params_invalid_limit(self):
        """Тест валидации с невалидным параметром limit."""
        # Act & Assert
        with pytest.raises(
            ValidationError, match="Limit must be a positive integer"
        ):
            self.validator.validate_pagination_params(0, 0)

    def test_validate_pagination_params_limit_too_high(self):
        """Тест валидации с слишком большим параметром limit."""
        # Act & Assert
        with pytest.raises(ValidationError, match="Limit cannot exceed 100"):
            self.validator.validate_pagination_params(0, 101)
