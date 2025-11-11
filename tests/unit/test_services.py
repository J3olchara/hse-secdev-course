"""
Unit тесты для сервисов.
"""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.schemas.user import UserLogin
from app.schemas.wish import WishCreate, WishUpdate
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.wish_service import WishService


class TestAuthService:
    """Тесты для AuthService."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_db = Mock(spec=Session)
        self.auth_service = AuthService(self.mock_db)
        # Мокируем репозиторий
        self.auth_service.user_repo = Mock()

    @patch('app.services.auth_service.verify_password')
    @patch('app.services.auth_service.create_access_token')
    def test_login_user_success(self, mock_create_token, mock_verify_password):
        """Тест успешного входа пользователя."""
        # Arrange
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.hashed_password = "hashed_password"
        mock_user.created_at = "2024-01-01"

        self.auth_service.user_repo.get_by_username_or_email.return_value = (
            mock_user
        )
        mock_verify_password.return_value = True
        mock_create_token.return_value = "test_token"

        login_data = UserLogin(username="testuser", password="password")

        # Act
        result = self.auth_service.login_user(login_data)

        # Assert
        assert result["access_token"] == "test_token"
        assert result["token_type"] == "bearer"
        assert result["user"]["username"] == "testuser"
        mock_verify_password.assert_called_once_with(
            "password", "hashed_password"
        )

    def test_login_user_invalid_username(self):
        """Тест входа с неверным именем пользователя."""
        # Arrange
        self.auth_service.user_repo.get_by_username_or_email.return_value = (
            None
        )
        login_data = UserLogin(username="nonexistent", password="password")

        # Act & Assert
        with pytest.raises(UnauthorizedError):
            self.auth_service.login_user(login_data)

    @patch('app.services.auth_service.verify_password')
    def test_login_user_invalid_password(self, mock_verify_password):
        """Тест входа с неверным паролем."""
        # Arrange
        mock_user = Mock()
        mock_user.hashed_password = "hashed_password"
        self.auth_service.user_repo.get_by_username_or_email.return_value = (
            mock_user
        )
        mock_verify_password.return_value = False

        login_data = UserLogin(username="testuser", password="wrong_password")

        # Act & Assert
        with pytest.raises(UnauthorizedError):
            self.auth_service.login_user(login_data)


class TestUserService:
    """Тесты для UserService."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_db = Mock(spec=Session)
        self.user_service = UserService(self.mock_db)
        # Мокируем репозиторий
        self.user_service.user_repo = Mock()

    def test_get_user_profile_success(self):
        """Тест успешного получения профиля пользователя."""
        # Arrange
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.created_at = "2024-01-01"

        self.user_service.user_repo.get.return_value = mock_user

        # Act
        result = self.user_service.get_user_profile(1)

        # Assert
        assert result.username == "testuser"
        assert result.email == "test@example.com"

    def test_get_user_profile_not_found(self):
        """Тест получения профиля несуществующего пользователя."""
        # Arrange
        self.user_service.user_repo.get.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            self.user_service.get_user_profile(999)


class TestWishService:
    """Тесты для WishService."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_db = Mock(spec=Session)
        self.wish_service = WishService(self.mock_db)
        # Мокируем репозитории
        self.wish_service.wish_repo = Mock()
        self.wish_service.user_repo = Mock()

    def test_create_wish_success(self):
        """Тест успешного создания желания."""
        # Arrange
        mock_user = Mock()
        mock_user.id = 1
        self.wish_service.user_repo.get.return_value = mock_user

        mock_wish = Mock()
        mock_wish.id = 1
        mock_wish.title = "Test Wish"
        mock_wish.description = "Test Description"
        mock_wish.user_id = 1
        mock_wish.created_at = "2024-01-01"
        mock_wish.updated_at = "2024-01-01"

        self.wish_service.wish_repo.create.return_value = mock_wish

        wish_data = WishCreate(
            title="Test Wish", description="Test Description"
        )

        # Act
        result = self.wish_service.create_wish(1, wish_data)

        # Assert
        assert result.title == "Test Wish"
        assert result.description == "Test Description"
        self.wish_service.wish_repo.create.assert_called_once()

    def test_get_wish_success(self):
        """Тест успешного получения желания."""
        # Arrange
        mock_wish = Mock()
        mock_wish.id = 1
        mock_wish.title = "Test Wish"
        mock_wish.description = "Test Description"
        mock_wish.user_id = 1
        mock_wish.created_at = "2024-01-01"
        mock_wish.updated_at = "2024-01-01"

        self.wish_service.wish_repo.get_by_user_and_id.return_value = mock_wish

        # Act
        result = self.wish_service.get_wish(1, 1)

        # Assert
        assert result.title == "Test Wish"
        assert result.description == "Test Description"
        self.wish_service.wish_repo.get_by_user_and_id.assert_called_once_with(
            1, 1
        )

    def test_get_wish_not_found(self):
        """Тест получения несуществующего желания."""
        # Arrange
        self.wish_service.wish_repo.get_by_user_and_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundError):
            self.wish_service.get_wish(1, 999)

    def test_update_wish_success(self):
        """Тест успешного обновления желания."""
        # Arrange
        mock_wish = Mock()
        mock_wish.id = 1
        mock_wish.title = "Updated Wish"
        mock_wish.description = "Updated Description"
        mock_wish.user_id = 1
        mock_wish.created_at = "2024-01-01"
        mock_wish.updated_at = "2024-01-01"

        self.wish_service.wish_repo.get_by_user_and_id.return_value = mock_wish
        self.wish_service.wish_repo.update.return_value = mock_wish

        wish_data = WishUpdate(title="Updated Wish")

        # Act
        result = self.wish_service.update_wish(1, 1, wish_data)

        # Assert
        assert result.title == "Updated Wish"
        self.wish_service.wish_repo.update.assert_called_once()

    def test_delete_wish_success(self):
        """Тест успешного удаления желания."""
        # Arrange
        self.wish_service.wish_repo.delete_by_user_and_id.return_value = True

        # Act
        result = self.wish_service.delete_wish(1, 1)

        # Assert
        assert result is True
        self.wish_service.wish_repo.delete_by_user_and_id.assert_called_once_with(
            1, 1
        )
