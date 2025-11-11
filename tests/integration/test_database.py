"""
Integration тесты для работы с базой данных.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import hash_password
from app.core.database import Base
from app.models.user import User
from app.models.wish import Wish
from app.repositories.user import UserRepository
from app.repositories.wish import WishRepository

# Создаем тестовую базу данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(scope="function")
def db_session():
    """Фикстура для тестовой сессии БД."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestUserRepositoryIntegration:
    """Integration тесты для UserRepository."""

    def test_create_user(self, db_session):
        """Тест создания пользователя."""
        user_repo = UserRepository(db_session)

        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }

        user = User(**user_data)
        created_user = user_repo.create(user)

        assert created_user.id is not None
        assert created_user.username == "testuser"
        assert created_user.email == "test@example.com"

    def test_get_user_by_username(self, db_session):
        """Тест получения пользователя по имени."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Получаем пользователя
        found_user = user_repo.get_by_username("testuser")

        assert found_user is not None
        assert found_user.username == "testuser"
        assert found_user.email == "test@example.com"

    def test_get_user_by_email(self, db_session):
        """Тест получения пользователя по email."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Получаем пользователя
        found_user = user_repo.get_by_email("test@example.com")

        assert found_user is not None
        assert found_user.username == "testuser"
        assert found_user.email == "test@example.com"

    def test_get_user_by_username_or_email(self, db_session):
        """Тест получения пользователя по имени или email."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Получаем по имени пользователя
        found_user = user_repo.get_by_username_or_email("testuser")
        assert found_user is not None
        assert found_user.username == "testuser"

        # Получаем по email
        found_user = user_repo.get_by_username_or_email("test@example.com")
        assert found_user is not None
        assert found_user.email == "test@example.com"

    def test_exists_by_username(self, db_session):
        """Тест проверки существования пользователя по имени."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Проверяем существование
        assert user_repo.exists_by_username("testuser") is True
        assert user_repo.exists_by_username("nonexistent") is False

    def test_exists_by_email(self, db_session):
        """Тест проверки существования пользователя по email."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Проверяем существование
        assert user_repo.exists_by_email("test@example.com") is True
        assert user_repo.exists_by_email("nonexistent@example.com") is False

    def test_update_user(self, db_session):
        """Тест обновления пользователя."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Обновляем пользователя
        update_data = {
            "username": "updateduser",
            "email": "updated@example.com",
        }
        updated_user = user_repo.update(user, update_data)

        assert updated_user.username == "updateduser"
        assert updated_user.email == "updated@example.com"

    def test_delete_user(self, db_session):
        """Тест удаления пользователя."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        # Удаляем пользователя
        result = user_repo.delete(user_id)

        assert result is True

        # Проверяем, что пользователь удален
        found_user = user_repo.get(user_id)
        assert found_user is None


class TestWishRepositoryIntegration:
    """Integration тесты для WishRepository."""

    def test_create_wish(self, db_session):
        """Тест создания желания."""
        wish_repo = WishRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Создаем желание
        wish_data = {
            "title": "Test Wish",
            "description": "Test Description",
            "user_id": user.id,
        }
        wish = Wish(**wish_data)
        created_wish = wish_repo.create(wish)

        assert created_wish.id is not None
        assert created_wish.title == "Test Wish"
        assert created_wish.description == "Test Description"
        assert created_wish.user_id == user.id

    def test_get_wish(self, db_session):
        """Тест получения желания."""
        wish_repo = WishRepository(db_session)

        # Создаем пользователя и желание
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        wish_data = {
            "title": "Test Wish",
            "description": "Test Description",
            "user_id": user.id,
        }
        wish = Wish(**wish_data)
        db_session.add(wish)
        db_session.commit()

        # Получаем желание
        found_wish = wish_repo.get(wish.id)

        assert found_wish is not None
        assert found_wish.title == "Test Wish"
        assert found_wish.user_id == user.id

    def test_get_user_wishes(self, db_session):
        """Тест получения желаний пользователя."""
        wish_repo = WishRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Создаем несколько желаний
        for i in range(3):
            wish_data = {
                "title": f"Test Wish {i}",
                "description": f"Test Description {i}",
                "user_id": user.id,
            }
            wish = Wish(**wish_data)
            db_session.add(wish)
        db_session.commit()

        # Получаем желания пользователя
        wishes = wish_repo.get_user_wishes(user.id)

        assert len(wishes) == 3
        assert all(wish.user_id == user.id for wish in wishes)

    def test_search_wishes(self, db_session):
        """Тест поиска желаний."""
        wish_repo = WishRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Создаем желания с разными названиями
        wish_titles = ["Python Book", "JavaScript Guide", "Python Tutorial"]
        for title in wish_titles:
            wish_data = {
                "title": title,
                "description": "Test Description",
                "user_id": user.id,
            }
            wish = Wish(**wish_data)
            db_session.add(wish)
        db_session.commit()

        # Ищем желания с "Python"
        python_wishes = wish_repo.search_wishes(user.id, "Python")

        assert len(python_wishes) == 2
        assert all("Python" in wish.title for wish in python_wishes)

    def test_update_wish(self, db_session):
        """Тест обновления желания."""
        wish_repo = WishRepository(db_session)

        # Создаем пользователя и желание
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        wish_data = {
            "title": "Original Title",
            "description": "Original Description",
            "user_id": user.id,
        }
        wish = Wish(**wish_data)
        db_session.add(wish)
        db_session.commit()

        # Обновляем желание
        update_data = {
            "title": "Updated Title",
            "description": "Updated Description",
        }
        updated_wish = wish_repo.update(wish, update_data)

        assert updated_wish.title == "Updated Title"
        assert updated_wish.description == "Updated Description"

    def test_delete_wish(self, db_session):
        """Тест удаления желания."""
        wish_repo = WishRepository(db_session)

        # Создаем пользователя и желание
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        wish_data = {
            "title": "Test Wish",
            "description": "Test Description",
            "user_id": user.id,
        }
        wish = Wish(**wish_data)
        db_session.add(wish)
        db_session.commit()
        wish_id = wish.id

        # Удаляем желание
        result = wish_repo.delete(wish_id)

        assert result is True

        # Проверяем, что желание удалено
        found_wish = wish_repo.get(wish_id)
        assert found_wish is None


class TestDatabaseRelationships:
    """Тесты для связей между таблицами."""

    def test_user_wishes_relationship(self, db_session):
        """Тест связи пользователя с желаниями."""
        user_repo = UserRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Создаем желания для пользователя
        for i in range(3):
            wish_data = {
                "title": f"Test Wish {i}",
                "description": f"Test Description {i}",
                "user_id": user.id,
            }
            wish = Wish(**wish_data)
            db_session.add(wish)
        db_session.commit()

        # Получаем пользователя с желаниями
        user_with_wishes = user_repo.get(user.id)

        assert len(user_with_wishes.wishes) == 3
        assert all(
            wish.owner == user_with_wishes for wish in user_with_wishes.wishes
        )

    def test_wish_owner_relationship(self, db_session):
        """Тест связи желания с владельцем."""
        wish_repo = WishRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Создаем желание
        wish_data = {
            "title": "Test Wish",
            "description": "Test Description",
            "user_id": user.id,
        }
        wish = Wish(**wish_data)
        db_session.add(wish)
        db_session.commit()

        # Получаем желание с владельцем
        wish_with_owner = wish_repo.get(wish.id)

        assert wish_with_owner.owner == user
        assert wish_with_owner.owner.username == "testuser"

    def test_cascade_delete(self, db_session):
        """Тест каскадного удаления пользователя с желаниями."""
        user_repo = UserRepository(db_session)
        wish_repo = WishRepository(db_session)

        # Создаем пользователя
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": hash_password("testpassword"),
        }
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()

        # Создаем желания для пользователя
        for i in range(3):
            wish_data = {
                "title": f"Test Wish {i}",
                "description": f"Test Description {i}",
                "user_id": user.id,
            }
            wish = Wish(**wish_data)
            db_session.add(wish)
        db_session.commit()

        # Удаляем пользователя
        user_repo.delete(user.id)

        # Проверяем, что желания тоже удалены
        wishes = wish_repo.get_user_wishes(user.id)
        assert len(wishes) == 0
