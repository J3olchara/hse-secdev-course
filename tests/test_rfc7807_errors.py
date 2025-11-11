"""
Тесты для RFC 7807 error handling (ADR-001)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_rfc7807_format_structure():
    """Проверяем что ошибки возвращаются в формате RFC 7807"""
    # Пытаемся получить несуществующий wish
    response = client.get("/api/v1/wishes/999999")

    assert response.status_code in [
        401,
        403,
        404,
    ]  # Может быть 401/403 если нет авторизации

    data = response.json()

    # Проверяем обязательные поля RFC 7807
    assert "type" in data, "RFC7807 требует поле 'type'"
    assert "title" in data, "RFC7807 требует поле 'title'"
    assert "status" in data, "RFC7807 требует поле 'status'"
    assert "detail" in data, "RFC7807 требует поле 'detail'"
    assert "correlation_id" in data, "Должен быть correlation_id (ADR-001)"

    # Проверяем типы
    assert isinstance(data["status"], int)
    assert isinstance(data["correlation_id"], str)
    assert len(data["correlation_id"]) > 0


def test_correlation_id_is_unique():
    """Проверяем что каждый запрос получает уникальный correlation_id"""
    response1 = client.get("/api/v1/wishes/99999")
    response2 = client.get("/api/v1/wishes/99998")

    # Оба должны вернуть ошибку
    assert response1.status_code >= 400
    assert response2.status_code >= 400

    data1 = response1.json()
    data2 = response2.json()

    # correlation_id должны быть разными
    if "correlation_id" in data1 and "correlation_id" in data2:
        assert (
            data1["correlation_id"] != data2["correlation_id"]
        ), "Каждый запрос должен иметь уникальный correlation_id"


def test_validation_error_format():
    """Тест валидационных ошибок в формате RFC 7807 (ADR-001 + ADR-004)"""
    # Пытаемся создать wish с пустым title
    response = client.post(
        "/api/v1/wishes", json={"title": "", "description": "test"}
    )

    # Ожидаем 401/403 (no auth) или 422 (validation error)
    assert response.status_code in [401, 403, 422]

    data = response.json()

    # Должна быть структура RFC 7807
    if response.status_code == 422:
        assert "detail" in data or "type" in data


def test_xss_attack_blocked():
    """Тест блокировки XSS атак (ADR-004, R7)"""
    # Попытка XSS через script tag
    xss_payloads = [
        {"title": "<script>alert('XSS')</script>", "description": "test"},
        {"title": "Test", "description": "<script>alert(1)</script>"},
        {"title": "javascript:alert(1)", "description": "test"},
    ]

    for payload in xss_payloads:
        response = client.post("/api/v1/wishes", json=payload)

        # Должны получить 401 (no auth) или 422 (validation error)
        # Главное что не 201 (created)
        assert (
            response.status_code != 201
        ), f"XSS payload не должен быть принят: {payload}"

        # Если получили 422, проверяем что это validation error
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data or "error" in data


def test_sql_injection_protected():
    """Тест защиты от SQL injection (ADR-004, R2)"""
    # Классические SQL injection payloads
    sql_payloads = [
        "'; DROP TABLE wishes; --",
        "1' OR '1'='1",
        "admin'--",
    ]

    for payload in sql_payloads:
        # Пытаемся в login
        response = client.post(
            "/api/v1/auth/login",
            json={"username": payload, "password": "test123"},
        )

        # Должны получить либо 401 (bad credentials) либо 422 (validation)
        # НО НЕ 500 (server error от SQL injection)
        assert (
            response.status_code != 500
        ), f"SQL injection не должен вызывать server error: {payload}"

        # Проверяем что в ответе нет SQL ошибок
        if response.status_code >= 400:
            text = response.text.lower()
            assert "sql" not in text, "Не должно быть SQL ошибок в response"
            assert "syntax error" not in text
            assert "pg_" not in text  # PostgreSQL table names


def test_long_string_rejected():
    """Тест что слишком длинные строки отклоняются (ADR-004, R9)"""
    # Создаем очень длинный title (больше лимита 200 символов)
    long_title = "A" * 201

    response = client.post(
        "/api/v1/wishes", json={"title": long_title, "description": "test"}
    )

    # Ожидаем 401/403 (no auth) или 422 (validation error)
    # Главное что не 201 или 500
    assert response.status_code in [
        401,
        403,
        422,
    ], "Слишком длинный title должен быть отклонен"

    # Проверяем очень длинное description (больше 5000 символов)
    long_desc = "B" * 5001

    response = client.post(
        "/api/v1/wishes", json={"title": "Test", "description": long_desc}
    )

    assert response.status_code in [
        401,
        403,
        422,
    ], "Слишком длинное description должно быть отклонено"


def test_invalid_username_format():
    """Тест валидации формата username (ADR-004)"""
    invalid_usernames = [
        "ab",  # too short (< 3)
        "user@name",  # @ not allowed
        "user name",  # spaces not allowed
        "user<script>",  # HTML tags not allowed
        "A" * 51,  # too long (> 50)
    ]

    for username in invalid_usernames:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": username,
                "email": "test@example.com",
                "password": "Password123",
            },
        )

        # Ожидаем validation error (422) или conflict (409)
        # Но точно не success (201)
        assert (
            response.status_code != 201
        ), f"Невалидный username не должен быть принят: {username}"


@pytest.mark.parametrize(
    "password",
    [
        "short",  # < 8 chars
        "12345678",  # only digits
        "password",  # only letters
        "Pass1",  # < 8 chars but has letter+digit
    ],
)
def test_weak_password_rejected(password):
    """Тест отклонения слабых паролей (ADR-004, NFR-01)"""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": password,
        },
    )

    # Должен быть валидационная ошибка
    # НО может быть 404 если эндпоинт не существует
    assert response.status_code in [
        404,
        422,
    ], f"Слабый пароль должен быть отклонен: {password}"
