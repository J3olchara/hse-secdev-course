"""
E2E тесты для полных сценариев использования.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.auth import hash_password
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User

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


def override_get_db():
    """Переопределяем зависимость для тестовой БД."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Фикстура для тестового клиента."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


class TestCompleteUserJourney:
    """Тесты для полного пользовательского сценария."""

    def test_user_registration_and_wish_management(self, client):
        """Полный сценарий: регистрация пользователя и управление желаниями."""
        from app.core.auth import create_access_token

        # 1. Создание пользователя в БД
        db = TestingSessionLocal()
        user = User(
            username="newuser",
            email="newuser@example.com",
            hashed_password=hash_password("newpassword123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()

        # 2. Создаем токен напрямую
        token_data = {"sub": str(user.id), "username": user.username}
        token = create_access_token(token_data)
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Получение профиля пользователя
        profile_response = client.get("/api/v1/auth/me", headers=headers)
        assert profile_response.status_code == 200
        user_data = profile_response.json()
        assert user_data["username"] == "newuser"
        assert user_data["email"] == "newuser@example.com"

        # 4. Создание первого желания
        wish1_data = {
            "title": "Купить новый ноутбук",
            "description": "MacBook Pro для работы",
        }
        wish1_response = client.post(
            "/api/v1/wishes", json=wish1_data, headers=headers
        )
        assert wish1_response.status_code == 200
        wish1 = wish1_response.json()
        assert wish1["title"] == "Купить новый ноутбук"
        assert wish1["description"] == "MacBook Pro для работы"
        wish1_id = wish1["id"]

        # 5. Создание второго желания
        wish2_data = {
            "title": "Изучить Python",
            "description": "Пройти курс по машинному обучению",
        }
        wish2_response = client.post(
            "/api/v1/wishes", json=wish2_data, headers=headers
        )
        assert wish2_response.status_code == 200
        wish2 = wish2_response.json()
        wish2_id = wish2["id"]

        # 6. Получение списка всех желаний
        wishes_response = client.get("/api/v1/wishes", headers=headers)
        assert wishes_response.status_code == 200
        wishes_data = wishes_response.json()
        assert len(wishes_data["wishes"]) == 2
        assert wishes_data["total"] == 2

        # 7. Получение конкретного желания
        get_wish_response = client.get(
            f"/api/v1/wishes/{wish1_id}", headers=headers
        )
        assert get_wish_response.status_code == 200
        retrieved_wish = get_wish_response.json()
        assert retrieved_wish["title"] == "Купить новый ноутбук"

        # 8. Обновление желания
        update_data = {
            "title": "Купить MacBook Pro M3",
            "description": "MacBook Pro M3 для работы и творчества",
        }
        update_response = client.patch(
            f"/api/v1/wishes/{wish1_id}", json=update_data, headers=headers
        )
        assert update_response.status_code == 200
        updated_wish = update_response.json()
        assert updated_wish["title"] == "Купить MacBook Pro M3"
        assert (
            updated_wish["description"]
            == "MacBook Pro M3 для работы и творчества"
        )

        # 9. Поиск желаний
        search_response = client.get(
            "/api/v1/wishes?search=MacBook", headers=headers
        )
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert len(search_data["wishes"]) == 1
        assert "MacBook" in search_data["wishes"][0]["title"]

        # 10. Удаление одного желания
        delete_response = client.delete(
            f"/api/v1/wishes/{wish2_id}", headers=headers
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Wish deleted successfully"

        # 11. Проверка, что желание удалено
        get_deleted_response = client.get(
            f"/api/v1/wishes/{wish2_id}", headers=headers
        )
        assert get_deleted_response.status_code == 404

        # 12. Проверка, что осталось только одно желание
        final_wishes_response = client.get("/api/v1/wishes", headers=headers)
        assert final_wishes_response.status_code == 200
        final_wishes_data = final_wishes_response.json()
        assert len(final_wishes_data["wishes"]) == 1
        assert (
            final_wishes_data["wishes"][0]["title"] == "Купить MacBook Pro M3"
        )

        # 13. Обновление токена
        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": token}
        )
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()["access_token"]
        assert new_token is not None
        assert len(new_token) > 0

        # 14. Выход из системы
        logout_response = client.post(
            "/api/v1/auth/logout", json={"token": new_token}, headers=headers
        )
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Successfully logged out"

    def test_multiple_users_isolation(self, client):
        """Тест изоляции данных между пользователями."""
        from app.core.auth import create_access_token

        # Создаем двух пользователей
        db = TestingSessionLocal()

        user1 = User(
            username="user1",
            email="user1@example.com",
            hashed_password=hash_password("password123"),
        )
        user2 = User(
            username="user2",
            email="user2@example.com",
            hashed_password=hash_password("password123"),
        )

        db.add(user1)
        db.add(user2)
        db.commit()
        db.refresh(user1)
        db.refresh(user2)
        db.close()

        # Создаем токены напрямую
        token1 = create_access_token(
            {"sub": str(user1.id), "username": user1.username}
        )
        headers1 = {"Authorization": f"Bearer {token1}"}

        token2 = create_access_token(
            {"sub": str(user2.id), "username": user2.username}
        )
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Первый пользователь создает желание
        wish1_data = {
            "title": "Желание пользователя 1",
            "description": "Это желание принадлежит первому пользователю",
        }
        wish1_response = client.post(
            "/api/v1/wishes", json=wish1_data, headers=headers1
        )
        assert wish1_response.status_code == 200
        wish1_id = wish1_response.json()["id"]

        # Второй пользователь создает желание
        wish2_data = {
            "title": "Желание пользователя 2",
            "description": "Это желание принадлежит второму пользователю",
        }
        wish2_response = client.post(
            "/api/v1/wishes", json=wish2_data, headers=headers2
        )
        assert wish2_response.status_code == 200
        wish2_id = wish2_response.json()["id"]

        # Первый пользователь видит только свои желания
        user1_wishes = client.get("/api/v1/wishes", headers=headers1)
        assert user1_wishes.status_code == 200
        user1_wishes_data = user1_wishes.json()
        assert len(user1_wishes_data["wishes"]) == 1
        assert (
            user1_wishes_data["wishes"][0]["title"] == "Желание пользователя 1"
        )

        # Второй пользователь видит только свои желания
        user2_wishes = client.get("/api/v1/wishes", headers=headers2)
        assert user2_wishes.status_code == 200
        user2_wishes_data = user2_wishes.json()
        assert len(user2_wishes_data["wishes"]) == 1
        assert (
            user2_wishes_data["wishes"][0]["title"] == "Желание пользователя 2"
        )

        # Первый пользователь не может получить желание второго пользователя
        forbidden_response = client.get(
            f"/api/v1/wishes/{wish2_id}", headers=headers1
        )
        assert (
            forbidden_response.status_code == 404
        )  # Не найдено, так как принадлежит другому пользователю

        # Второй пользователь не может получить желание первого пользователя
        forbidden_response2 = client.get(
            f"/api/v1/wishes/{wish1_id}", headers=headers2
        )
        assert forbidden_response2.status_code == 404

    def test_pagination_and_search_scenarios(self, client):
        """Тест сценариев пагинации и поиска."""
        from app.core.auth import create_access_token

        # Создаем пользователя
        db = TestingSessionLocal()
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()

        # Создаем токен напрямую
        token = create_access_token(
            {"sub": str(user.id), "username": user.username}
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Создаем 10 желаний с разными названиями
        wish_titles = [
            "Купить Python книгу",
            "Изучить JavaScript",
            "Python курс по Django",
            "Купить новый телефон",
            "JavaScript фреймворк React",
            "Python библиотека NumPy",
            "Купить велосипед",
            "Изучить TypeScript",
            "Python машинное обучение",
            "Купить наушники",
        ]

        created_wishes = []
        for title in wish_titles:
            wish_data = {
                "title": title,
                "description": f"Описание для {title}",
            }
            response = client.post(
                "/api/v1/wishes", json=wish_data, headers=headers
            )
            assert response.status_code == 200
            created_wishes.append(response.json())

        # Тест пагинации - первая страница
        page1_response = client.get(
            "/api/v1/wishes?skip=0&limit=5", headers=headers
        )
        assert page1_response.status_code == 200
        page1_data = page1_response.json()
        assert len(page1_data["wishes"]) == 5
        assert page1_data["page"] == 0
        assert page1_data["size"] == 5
        assert page1_data["total"] == 10

        # Тест пагинации - вторая страница
        page2_response = client.get(
            "/api/v1/wishes?skip=5&limit=5", headers=headers
        )
        assert page2_response.status_code == 200
        page2_data = page2_response.json()
        assert len(page2_data["wishes"]) == 5
        assert page2_data["page"] == 1
        assert page2_data["size"] == 5

        # Тест поиска по "Python"
        python_search = client.get(
            "/api/v1/wishes?search=Python", headers=headers
        )
        assert python_search.status_code == 200
        python_data = python_search.json()
        assert len(python_data["wishes"]) == 4  # 4 желания содержат "Python"
        assert all("Python" in wish["title"] for wish in python_data["wishes"])

        # Тест поиска по "Купить"
        buy_search = client.get(
            "/api/v1/wishes?search=Купить", headers=headers
        )
        assert buy_search.status_code == 200
        buy_data = buy_search.json()
        assert len(buy_data["wishes"]) == 4  # 4 желания содержат "Купить"
        assert all("Купить" in wish["title"] for wish in buy_data["wishes"])

        # Тест поиска по "JavaScript"
        js_search = client.get(
            "/api/v1/wishes?search=JavaScript", headers=headers
        )
        assert js_search.status_code == 200
        js_data = js_search.json()
        assert len(js_data["wishes"]) == 2  # 2 желания содержат "JavaScript"

        # Тест поиска с пагинацией
        search_paginated = client.get(
            "/api/v1/wishes?search=Python&skip=0&limit=2", headers=headers
        )
        assert search_paginated.status_code == 200
        search_paginated_data = search_paginated.json()
        assert len(search_paginated_data["wishes"]) == 2
        assert all(
            "Python" in wish["title"]
            for wish in search_paginated_data["wishes"]
        )

    def test_error_handling_scenarios(self, client):
        """Тест сценариев обработки ошибок."""
        from app.core.auth import create_access_token

        # Создаем пользователя
        db = TestingSessionLocal()
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hash_password("password123"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.close()

        # Создаем токен напрямую
        token = create_access_token(
            {"sub": str(user.id), "username": user.username}
        )
        headers = {"Authorization": f"Bearer {token}"}

        # Тест создания желания с пустым заголовком
        invalid_wish = {"title": "", "description": "Test"}
        response = client.post(
            "/api/v1/wishes", json=invalid_wish, headers=headers
        )
        assert response.status_code == 422  # Pydantic validation error

        # Тест создания желания без заголовка
        invalid_wish2 = {"description": "Test"}
        response = client.post(
            "/api/v1/wishes", json=invalid_wish2, headers=headers
        )
        assert response.status_code == 422  # Validation error

        # Тест получения несуществующего желания
        response = client.get("/api/v1/wishes/99999", headers=headers)
        assert response.status_code == 404

        # Тест обновления несуществующего желания
        update_data = {"title": "Updated"}
        response = client.patch(
            "/api/v1/wishes/99999", json=update_data, headers=headers
        )
        assert response.status_code == 404

        # Тест удаления несуществующего желания
        response = client.delete("/api/v1/wishes/99999", headers=headers)
        assert response.status_code == 404

        # Тест запроса без авторизации
        response = client.get("/api/v1/wishes")
        assert (
            response.status_code == 403
        )  # HTTPBearer возвращает 403 без токена

        # Тест с неверным токеном
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/v1/wishes", headers=invalid_headers)
        assert response.status_code == 401

        # Тест с истекшим токеном (симулируем)
        expired_headers = {"Authorization": "Bearer expired_token"}
        response = client.get("/api/v1/wishes", headers=expired_headers)
        assert response.status_code == 401
