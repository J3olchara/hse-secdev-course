"""
Централизованная карта кодов ошибок для RFC7807 Problem Details (ADR-005, NFR-02).

Все ошибки API должны использовать эти коды для консистентности.
"""

from typing import Dict


class ErrorCode:
    """Коды ошибок приложения с человеко-читаемыми описаниями."""

    # Общие ошибки (1000-1999)
    INTERNAL_ERROR = "internal_error"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    BAD_REQUEST = "bad_request"

    # Аутентификация (2000-2999)
    UNAUTHORIZED = "unauthorized"
    INVALID_CREDENTIALS = "invalid_credentials"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    FORBIDDEN = "forbidden"

    # Бизнес логика (3000-3999)
    CONFLICT = "conflict"
    BUSINESS_ERROR = "business_error"
    RESOURCE_LOCKED = "resource_locked"

    # Безопасность (4000-4999)
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    XSS_DETECTED = "xss_detected"
    SQL_INJECTION_DETECTED = "sql_injection_detected"

    # База данных (5000-5999)
    DATABASE_ERROR = "database_error"
    CONSTRAINT_VIOLATION = "constraint_violation"

    # Валидация (6000-6999)
    INVALID_INPUT = "invalid_input"
    MISSING_FIELD = "missing_field"
    FIELD_TOO_LONG = "field_too_long"
    INVALID_FORMAT = "invalid_format"
    EXTRA_FIELDS_NOT_ALLOWED = "extra_fields_not_allowed"


# Карта кодов ошибок с описаниями для клиентов
ERROR_DESCRIPTIONS: Dict[str, str] = {
    # Общие ошибки
    ErrorCode.INTERNAL_ERROR: "An internal server error occurred. Please try again later.",
    ErrorCode.VALIDATION_ERROR: "The request contains invalid data.",
    ErrorCode.NOT_FOUND: "The requested resource was not found.",
    ErrorCode.BAD_REQUEST: "The request is malformed or contains invalid parameters.",
    # Аутентификация
    ErrorCode.UNAUTHORIZED: "Authentication is required to access this resource.",
    ErrorCode.INVALID_CREDENTIALS: "The provided credentials are invalid.",
    ErrorCode.TOKEN_EXPIRED: "Your authentication token has expired. Please login again.",
    ErrorCode.TOKEN_INVALID: "The authentication token is invalid or malformed.",
    ErrorCode.FORBIDDEN: "You do not have permission to access this resource.",
    # Бизнес логика
    ErrorCode.CONFLICT: "The request conflicts with the current state of the resource.",
    ErrorCode.BUSINESS_ERROR: "A business rule violation occurred.",
    ErrorCode.RESOURCE_LOCKED: "The resource is currently locked by another operation.",
    # Безопасность
    ErrorCode.RATE_LIMIT_EXCEEDED: "Too many requests. Please slow down and try again later.",
    ErrorCode.SUSPICIOUS_ACTIVITY: "Suspicious activity detected. Your request has been blocked.",
    ErrorCode.XSS_DETECTED: "Potentially malicious content detected in your input.",
    ErrorCode.SQL_INJECTION_DETECTED: "Potentially malicious SQL detected in your input.",
    # База данных
    ErrorCode.DATABASE_ERROR: "A database error occurred. Please try again later.",
    ErrorCode.CONSTRAINT_VIOLATION: "The operation violates a database constraint.",
    # Валидация
    ErrorCode.INVALID_INPUT: "One or more input fields are invalid.",
    ErrorCode.MISSING_FIELD: "A required field is missing.",
    ErrorCode.FIELD_TOO_LONG: "One or more fields exceed the maximum allowed length.",
    ErrorCode.INVALID_FORMAT: "The format of one or more fields is invalid.",
    ErrorCode.EXTRA_FIELDS_NOT_ALLOWED: "Extra fields are not allowed in the request.",
}


def get_error_description(code: str) -> str:
    """
    Получить человеко-читаемое описание ошибки по коду.

    Args:
        code: Код ошибки

    Returns:
        Описание ошибки или общее сообщение если код не найден
    """
    return ERROR_DESCRIPTIONS.get(code, "An error occurred.")
