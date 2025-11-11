"""
Integration тесты для API эндпоинтов.
"""


class TestAuthEndpoints:
    """Тесты для эндпоинтов аутентификации."""

    def test_get_current_user(self, client, auth_headers):
        """Тест получения текущего пользователя."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_unauthorized(self, client):
        """Тест получения текущего пользователя без авторизации."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 403


class TestWishEndpoints:
    """Тесты для эндпоинтов желаний."""

    def test_create_wish_success(self, client, auth_headers):
        """Тест успешного создания желания."""
        wish_data = {"title": "Test Wish", "description": "Test Description"}
        response = client.post(
            "/api/v1/wishes", json=wish_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Wish"
        assert data["description"] == "Test Description"
        assert "id" in data
        assert "created_at" in data

    def test_create_wish_unauthorized(self, client):
        """Тест создания желания без авторизации."""
        wish_data = {"title": "Test Wish", "description": "Test Description"}
        response = client.post("/api/v1/wishes", json=wish_data)

        assert response.status_code == 403

    def test_get_wish_success(self, client, auth_headers):
        """Тест успешного получения желания."""
        # Сначала создаем желание
        wish_data = {"title": "Test Wish", "description": "Test Description"}
        create_response = client.post(
            "/api/v1/wishes", json=wish_data, headers=auth_headers
        )
        wish_id = create_response.json()["id"]

        # Получаем желание
        response = client.get(
            f"/api/v1/wishes/{wish_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Wish"
        assert data["description"] == "Test Description"

    def test_get_wishes_list(self, client, auth_headers):
        """Тест получения списка желаний."""
        # Создаем несколько желаний
        for i in range(3):
            wish_data = {
                "title": f"Test Wish {i}",
                "description": f"Test Description {i}",
            }
            client.post("/api/v1/wishes", json=wish_data, headers=auth_headers)

        # Получаем список желаний
        response = client.get("/api/v1/wishes", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data["wishes"]) == 3
        assert data["total"] == 3

    def test_update_wish_success(self, client, auth_headers):
        """Тест успешного обновления желания."""
        # Создаем желание
        wish_data = {
            "title": "Original Title",
            "description": "Original Description",
        }
        create_response = client.post(
            "/api/v1/wishes", json=wish_data, headers=auth_headers
        )
        wish_id = create_response.json()["id"]

        # Обновляем желание
        update_data = {
            "title": "Updated Title",
            "description": "Updated Description",
        }
        response = client.patch(
            f"/api/v1/wishes/{wish_id}", json=update_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["description"] == "Updated Description"

    def test_delete_wish_success(self, client, auth_headers):
        """Тест успешного удаления желания."""
        # Создаем желание
        wish_data = {"title": "Test Wish", "description": "Test Description"}
        create_response = client.post(
            "/api/v1/wishes", json=wish_data, headers=auth_headers
        )
        wish_id = create_response.json()["id"]

        # Удаляем желание
        response = client.delete(
            f"/api/v1/wishes/{wish_id}", headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Wish deleted successfully"

        # Проверяем, что желание удалено
        get_response = client.get(
            f"/api/v1/wishes/{wish_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_get_wishes_with_pagination(self, client, auth_headers):
        """Тест получения желаний с пагинацией."""
        # Создаем 5 желаний
        for i in range(5):
            wish_data = {
                "title": f"Test Wish {i}",
                "description": f"Test Description {i}",
            }
            client.post("/api/v1/wishes", json=wish_data, headers=auth_headers)

        # Получаем первые 2 желания
        response = client.get(
            "/api/v1/wishes?skip=0&limit=2", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["wishes"]) == 2
        assert data["page"] == 0
        assert data["size"] == 2

    def test_get_wishes_with_search(self, client, auth_headers):
        """Тест поиска желаний."""
        # Создаем желания с разными названиями
        wish_titles = ["Python Book", "JavaScript Guide", "Python Tutorial"]
        for title in wish_titles:
            wish_data = {"title": title, "description": "Test Description"}
            client.post("/api/v1/wishes", json=wish_data, headers=auth_headers)

        # Ищем желания с "Python"
        response = client.get(
            "/api/v1/wishes?search=Python", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["wishes"]) == 2
        assert all("Python" in wish["title"] for wish in data["wishes"])
