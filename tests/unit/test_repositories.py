"""
Unit тесты для репозиториев.
"""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.wish import Wish
from app.repositories.user import UserRepository
from app.repositories.wish import WishRepository


class TestUserRepository:
    """Тесты для UserRepository."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_db = Mock(spec=Session)
        self.user_repo = UserRepository(self.mock_db)

    def test_get_by_username_success(self):
        """Тест успешного получения пользователя по имени."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.user_repo.get_by_username("testuser")

        # Assert
        assert result == mock_user
        self.mock_db.query.assert_called_once_with(User)

    def test_get_by_username_not_found(self):
        """Тест получения несуществующего пользователя по имени."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.user_repo.get_by_username("nonexistent")

        # Assert
        assert result is None

    def test_get_by_email_success(self):
        """Тест успешного получения пользователя по email."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.user_repo.get_by_email("test@example.com")

        # Assert
        assert result == mock_user
        self.mock_db.query.assert_called_once_with(User)

    def test_get_by_username_or_email_username(self):
        """Тест получения пользователя по имени пользователя."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.user_repo.get_by_username_or_email("testuser")

        # Assert
        assert result == mock_user

    def test_get_by_username_or_email_email(self):
        """Тест получения пользователя по email."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.user_repo.get_by_username_or_email("test@example.com")

        # Assert
        assert result == mock_user

    def test_exists_by_username_true(self):
        """Тест проверки существования пользователя по имени (существует)."""
        # Arrange
        mock_user = Mock(spec=User)
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.user_repo.exists_by_username("testuser")

        # Assert
        assert result is True

    def test_exists_by_username_false(self):
        """Тест проверки существования пользователя (не существует)."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.user_repo.exists_by_username("nonexistent")

        # Assert
        assert result is False

    def test_database_error_handling(self):
        """Тест обработки ошибок базы данных."""
        # Arrange
        self.mock_db.query.side_effect = SQLAlchemyError("Database error")

        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            self.user_repo.get_by_username("testuser")


class TestWishRepository:
    """Тесты для WishRepository."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_db = Mock(spec=Session)
        self.wish_repo = WishRepository(self.mock_db)

    def test_get_by_user_id_success(self):
        """Тест успешного получения желаний пользователя."""
        # Arrange
        mock_wish1 = Mock(spec=Wish)
        mock_wish2 = Mock(spec=Wish)

        mock_query = Mock()
        filter_result = mock_query.filter.return_value
        offset_result = filter_result.offset.return_value
        limit_result = offset_result.limit.return_value
        limit_result.all.return_value = [mock_wish1, mock_wish2]
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.wish_repo.get_by_user_id(1, skip=0, limit=10)

        # Assert
        assert len(result) == 2
        assert result[0] == mock_wish1
        assert result[1] == mock_wish2
        self.mock_db.query.assert_called_once_with(Wish)

    def test_get_by_user_and_id_success(self):
        """Тест успешного получения желания пользователя по ID."""
        # Arrange
        mock_wish = Mock(spec=Wish)
        mock_wish.id = 1
        mock_wish.user_id = 1

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_wish
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.wish_repo.get_by_user_and_id(1, 1)

        # Assert
        assert result == mock_wish
        self.mock_db.query.assert_called_once_with(Wish)

    def test_search_by_title_success(self):
        """Тест успешного поиска желаний по названию."""
        # Arrange
        mock_wish1 = Mock(spec=Wish)
        mock_wish1.title = "Test Wish 1"
        mock_wish2 = Mock(spec=Wish)
        mock_wish2.title = "Another Wish"

        mock_query = Mock()
        filter_result = mock_query.filter.return_value
        offset_result = filter_result.offset.return_value
        limit_result = offset_result.limit.return_value
        limit_result.all.return_value = [mock_wish1, mock_wish2]
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.wish_repo.search_by_title(1, "Test", skip=0, limit=10)

        # Assert
        assert len(result) == 2
        self.mock_db.query.assert_called_once_with(Wish)

    def test_search_by_title_empty(self):
        """Тест поиска желаний без результатов."""
        # Arrange
        mock_query = Mock()
        filter_result = mock_query.filter.return_value
        offset_result = filter_result.offset.return_value
        limit_result = offset_result.limit.return_value
        limit_result.all.return_value = []
        self.mock_db.query.return_value = mock_query

        # Act
        result = self.wish_repo.search_by_title(
            1, "Nonexistent", skip=0, limit=10
        )

        # Assert
        assert len(result) == 0

    def test_delete_by_user_and_id_success(self):
        """Тест успешного удаления желания."""
        # Arrange
        mock_wish = Mock(spec=Wish)
        mock_wish.id = 1
        mock_wish.user_id = 1

        # Мокируем метод get_by_user_and_id
        with patch.object(
            self.wish_repo, 'get_by_user_and_id', return_value=mock_wish
        ):
            # Act
            result = self.wish_repo.delete_by_user_and_id(1, 1)

            # Assert
            assert result is True
            self.mock_db.delete.assert_called_once_with(mock_wish)
            self.mock_db.commit.assert_called_once()

    def test_delete_by_user_and_id_not_found(self):
        """Тест удаления несуществующего желания."""
        # Arrange
        with patch.object(
            self.wish_repo, 'get_by_user_and_id', return_value=None
        ):
            # Act
            result = self.wish_repo.delete_by_user_and_id(1, 999)

            # Assert
            assert result is False
