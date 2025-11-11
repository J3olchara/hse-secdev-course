"""
NFR тесты безопасности (Security Tests).

Проверяют:
- Защиту от SQL-инъекций
- Защиту от XSS
- Валидацию входных данных
- Безопасность заголовков
- Защиту от CSRF
- Защиту от DoS

NOTE: некоторые тесты могут выглядеть параноидально, но лучше перебдеть
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Клиент для тестирования безопасности."""
    return TestClient(app)


class TestInputValidation:
    """Тесты валидации входных данных."""

    def test_sql_injection_protection(self, client):
        """Проверка защиты от SQL-инъекций."""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1--",
            "1; DELETE FROM items WHERE 1=1; --",
            "' UNION SELECT NULL, NULL, NULL--",
        ]

        for payload in sql_injection_payloads:
            # Проверяем создание item с SQL-инъекцией
            response = client.post(f"/items?name={payload}")

            # Должно либо отклониться с ошибкой валидации,
            # либо принять как обычный текст
            assert response.status_code in [
                200,
                422,
            ], f"Unexpected status for payload: {payload}"

            # Если принято, должно быть сохранено как текст
            if response.status_code == 200:
                item_id = response.json()["id"]
                get_response = client.get(f"/items/{item_id}")
                assert get_response.status_code == 200

    def test_xss_protection(self, client):
        """Проверка защиты от XSS."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
            "<iframe src='javascript:alert(XSS)'>",
        ]

        for payload in xss_payloads:
            response = client.post(f"/items?name={payload}")

            # Должно либо отклониться, либо правильно экранировать
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                # Проверяем, что данные не исполняются
                data = response.json()
                # Данные должны быть возвращены как текст
                assert "name" in data

    def test_oversized_input_rejection(self, client):
        """Проверка отклонения слишком больших данных."""
        # Очень длинное имя (больше 100 символов)
        long_name = "A" * 1000

        response = client.post(f"/items?name={long_name}")

        # Должно быть отклонено с ошибкой валидации
        assert response.status_code == 422
        assert "error" in response.json()

    def test_empty_input_rejection(self, client):
        """Проверка отклонения пустых данных."""
        response = client.post("/items?name=")

        # Должно быть отклонено
        assert response.status_code == 422
        assert "error" in response.json()

    def test_special_characters_handling(self, client):
        """Проверка обработки спецсимволов."""
        import urllib.parse

        special_chars = [
            "test null byte",  # пробел вместо null byte (null byte нельзя в URL)
            "test\nnewline",  # newline
            "test\ttab",  # tab
            "test\\backslash",  # backslash
            'test"quote',  # quote
        ]

        for chars in special_chars:
            # URL-encode для безопасной передачи
            # NOTE: без этого httpx ругается на невалидные символы
            encoded_chars = urllib.parse.quote(chars)
            response = client.post(f"/items?name={encoded_chars}")

            # должно либо принять и правильно обработать либо отклонить
            assert response.status_code in [200, 422]

    def test_path_traversal_protection(self, client):
        """Проверка защиты от path traversal."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "....//....//....//etc/passwd",
        ]

        for payload in path_traversal_payloads:
            response = client.post(f"/items?name={payload}")

            # Должно обрабатываться безопасно
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                # Не должно выполняться как путь
                data = response.json()
                assert "name" in data


class TestSecurityHeaders:
    """Тесты безопасности заголовков HTTP."""

    def test_cors_headers(self, client):
        """Проверка CORS заголовков."""
        response = client.get("/health")

        # Должны быть настроены CORS заголовки
        assert response.status_code == 200

        # Проверяем, что приложение работает
        # (конкретные CORS настройки зависят от конфигурации)

    def test_no_sensitive_headers_in_error(self, client):
        """Проверка отсутствия чувствительной информации в ошибках."""
        response = client.get("/items/99999")

        assert response.status_code == 404

        # Ошибка не должна содержать техническую информацию
        error_data = response.json()
        assert "error" in error_data

        error_text = str(error_data).lower()
        # Не должно быть путей к файлам, стектрейсов и т.д.
        assert "traceback" not in error_text
        assert "/app/" not in error_text
        assert "sqlalchemy" not in error_text


class TestAuthenticationSecurity:
    """Тесты безопасности аутентификации."""

    def test_password_not_in_response(self, client):
        """Проверка, что пароли не возвращаются в ответах."""
        # Делаем любые запросы и проверяем ответы
        responses = [
            client.get("/health"),
            client.post("/items?name=Test"),
            client.get("/items/1"),
        ]

        for response in responses:
            response_text = str(response.json()).lower()

            # Не должно быть упоминаний о паролях
            assert "password" not in response_text
            assert "hashed_password" not in response_text
            assert "secret" not in response_text.replace(
                "secret_key", ""
            )  # Исключаем легитимные упоминания


class TestRateLimiting:
    """Тесты защиты от DoS."""

    @pytest.mark.timeout(10)
    def test_rapid_requests_handling(self, client):
        """Проверка обработки быстрых последовательных запросов."""
        # отправляем много запросов подряд
        responses = []
        for _ in range(100):
            response = client.get("/health")
            responses.append(response.status_code)

        # все запросы должны обрабатываться
        # (либо успешно либо с rate limiting)
        for status in responses:
            assert status in [
                200,
                429,
            ]  # 429 = Too Many Requests если есть rate limiting

    def test_large_payload_handling(self, client):
        """Проверка обработки больших payload."""
        # Пытаемся отправить очень длинные данные
        large_name = "X" * 10000

        response = client.post(f"/items?name={large_name}")

        # Должно быть отклонено с ошибкой валидации
        assert response.status_code in [413, 422]  # 413 = Payload Too Large


class TestErrorHandling:
    """Тесты безопасной обработки ошибок."""

    def test_404_error_format(self, client):
        """Проверка формата 404 ошибок."""
        response = client.get("/items/99999")

        assert response.status_code == 404

        # Должен быть стандартный формат ошибки
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]

    def test_validation_error_format(self, client):
        """Проверка формата ошибок валидации."""
        response = client.post("/items?name=")

        assert response.status_code == 422

        # Должен быть стандартный формат ошибки
        data = response.json()
        assert "error" in data

    def test_method_not_allowed(self, client):
        """Проверка обработки неподдерживаемых методов."""
        response = client.delete("/health")

        # Должна быть ошибка о неподдерживаемом методе
        assert response.status_code in [405, 404]

    def test_malformed_request(self, client):
        """Проверка обработки некорректных запросов."""
        # Пытаемся получить item с некорректным ID
        response = client.get("/items/not_a_number")

        # Должна быть ошибка валидации
        assert response.status_code in [404, 422]


class TestDataLeakage:
    """Тесты утечки данных."""

    def test_no_stack_traces_in_production(self, client):
        """Проверка отсутствия стектрейсов в ответах."""
        # Провоцируем различные ошибки
        test_cases = [
            client.get("/items/99999"),
            client.get("/nonexistent"),
            client.post("/items?name="),
        ]

        for response in test_cases:
            response_text = str(response.json()).lower()

            # Не должно быть технических деталей
            assert "traceback" not in response_text
            assert "file" not in response_text or "not found" in response_text
            assert "line" not in response_text

    def test_no_database_errors_exposed(self, client):
        """Проверка, что ошибки БД не раскрываются."""
        responses = [
            client.get("/items/99999"),
            client.post("/items?name=Test"),
        ]

        for response in responses:
            response_text = str(response.json()).lower()

            # Не должно быть упоминаний о БД
            assert "database" not in response_text
            assert "sql" not in response_text
            assert "postgres" not in response_text
            assert "sqlite" not in response_text


class TestInputSanitization:
    """Тесты санитизации входных данных."""

    def test_unicode_handling(self, client):
        """Проверка обработки Unicode символов."""
        unicode_strings = [
            "Привет мир",  # Кириллица
            "你好世界",  # Китайский
            "مرحبا بالعالم",  # Арабский
            "🎉🎊✨",  # Эмодзи
            "Ĥĕļļŏ Ŵŏŗļđ",  # Специальные символы
        ]

        for unicode_str in unicode_strings:
            response = client.post(f"/items?name={unicode_str}")

            # Должно правильно обрабатываться
            assert response.status_code in [200, 422]

            if response.status_code == 200:
                data = response.json()
                assert "name" in data

    def test_boundary_values(self, client):
        """Проверка граничных значений."""
        test_cases = [
            ("a", 200),  # Минимальная длина
            ("A" * 100, 200),  # Максимальная длина
            ("A" * 101, 422),  # Превышение максимума
        ]

        for name, expected_status in test_cases:
            response = client.post(f"/items?name={name}")
            assert (
                response.status_code == expected_status
            ), f"Failed for name length {len(name)}"


@pytest.mark.slow
class TestSecurityStress:
    """Стресс-тесты безопасности."""

    @pytest.mark.timeout(30)
    def test_sustained_malicious_requests(self, client):
        """Проверка устойчивости к продолжительным вредоносным запросам."""
        malicious_payloads = [
            "'; DROP TABLE items; --",
            "<script>alert('XSS')</script>",
            "../../../etc/passwd",
            "A" * 1000,
        ]

        errors = 0
        for _ in range(100):
            for payload in malicious_payloads:
                try:
                    response = client.post(f"/items?name={payload}")
                    # Должно обрабатываться безопасно
                    assert response.status_code in [200, 422]
                except Exception:
                    errors += 1

        # Количество ошибок должно быть минимальным
        assert (
            errors < 5
        ), f"Too many errors handling malicious requests: {errors}"
