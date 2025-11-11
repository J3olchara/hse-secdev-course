"""
Интеграционные тесты для подтверждения NFR требований безопасности.
"""


class TestNFRRequirements:
    """Тесты для подтверждения нефункциональных требований безопасности."""

    def test_nfr06_rate_limiting_auth(self, client):
        """Тест NFR-06: Проверка rate limiting для аутентификации."""
        # Делаем несколько неудачных попыток входа
        for i in range(3):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "nonexistent", "password": "WrongPass123"},
            )

            if i < 2:
                # Первые 2 попытки должны вернуть 401
                assert response.status_code == 401
            else:
                # 3-я попытка должна быть заблокирована
                assert response.status_code == 429
                assert "Too Many Requests" in response.json()["title"]

    def test_nfr08_input_validation_sql_injection(self, client, auth_headers):
        """Тест NFR-08: Проверка защиты от SQL injection."""
        # Тестируем различные SQL injection payloads
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT NULL, NULL, NULL--",
            "'; DELETE FROM wishes WHERE '1'='1'; --",
        ]

        for payload in sql_payloads:
            # Пытаемся создать желание с вредоносным контентом
            wish_data = {"title": payload, "description": "Test Description"}

            response = client.post(
                "/api/v1/wishes", json=wish_data, headers=auth_headers
            )

            # Запрос должен либо принять данные как обычный текст,
            # либо отклонить с ошибкой валидации
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                # Если принято, проверяем что данные сохранены как текст
                data = response.json()
                assert "title" in data
                # Заголовок должен быть сохранен как есть (без выполнения)
                assert data["title"] == payload

    def test_nfr08_input_validation_xss(self, client, auth_headers):
        """Тест NFR-08: Проверка защиты от XSS атак."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src='javascript:alert(XSS)'>",
        ]

        for payload in xss_payloads:
            wish_data = {"title": "Test", "description": payload}

            response = client.post(
                "/api/v1/wishes", json=wish_data, headers=auth_headers
            )

            # Запрос должен либо принять, либо отклонить
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                # Данные должны быть сохранены как текст (не исполнены)
                data = response.json()
                assert data["description"] == payload

    def test_nfr08_input_validation_length_limits(self, client, auth_headers):
        """Тест NFR-08: Проверка ограничений длины входных данных."""
        # Тестируем слишком длинные данные
        long_title = "A" * 201  # Превышаем ограничение в 200 символов
        long_description = "B" * 1001  # Превышаем ограничение в 1000 символов

        wish_data = {"title": long_title, "description": long_description}

        response = client.post(
            "/api/v1/wishes", json=wish_data, headers=auth_headers
        )

        # Должно быть отклонено с ошибкой валидации
        assert response.status_code == 422
        error_data = response.json()
        assert "Unprocessable Entity" in error_data["title"]

    def test_error_format_correlation_id_consistency(self, client):
        """Тест согласованности correlation_id в ошибках."""
        # Делаем несколько запросов с ошибками
        responses = []
        for i in range(3):
            response = client.get("/api/v1/wishes/999")
            responses.append(response.json())

        # Каждый ответ должен иметь уникальный correlation_id
        correlation_ids = [r["correlation_id"] for r in responses]
        assert len(set(correlation_ids)) == len(
            correlation_ids
        )  # Все уникальные

        # Формат timestamp должен быть ISO 8601
        for response_data in responses:
            timestamp = response_data["timestamp"]
            # Простая проверка формата ISO 8601
            assert "T" in timestamp or "Z" in timestamp

    def test_rate_limiting_headers(self, client):
        """Тест наличия правильных заголовков в ответах rate limiting."""
        # Делаем запросы до достижения лимита
        for i in range(2):
            response = client.post(
                "/api/v1/auth/login",
                json={"username": "nonexistent", "password": "WrongPass123"},
            )
            assert response.status_code == 401

        # Третий запрос должен вернуть 429 с заголовком Retry-After
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "WrongPass123"},
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] == "60"
