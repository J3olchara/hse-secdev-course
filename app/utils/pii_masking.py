"""
Утилиты для маскирования PII (Personally Identifiable Information) в логах и ответах.
ADR-005, NFR-02 - защита от утечки чувствительных данных.
"""

import re
from typing import Any


def mask_email(email: str) -> str:
    """
    Маскирует email адрес, оставляя только первый символ и домен.
    Пример: test@example.com -> t***@example.com
    """
    if not email or '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    if len(local) <= 1:
        return f"{local}***@{domain}"
    return f"{local[0]}***@{domain}"


def mask_password(password: str) -> str:
    """
    Полностью маскирует пароль.
    """
    return "***REDACTED***"


def mask_token(token: str) -> str:
    """
    Маскирует токен, показывая только последние 4 символа.
    """
    if not token or len(token) <= 4:
        return "***"
    return f"***{token[-4:]}"


def mask_pii_in_string(text: str) -> str:
    """
    Автоматически находит и маскирует PII в строке (email, возможные токены).
    """
    # Маскируем email адреса
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    text = re.sub(email_pattern, lambda m: mask_email(m.group()), text)
    
    # Маскируем длинные строки похожие на токены (например, JWT)
    # JWT обычно содержит точки и имеет длину > 20 символов
    token_pattern = r'\b[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\b'
    text = re.sub(token_pattern, '***JWT_TOKEN***', text)
    
    return text


def mask_dict_values(data: dict[str, Any], sensitive_keys: set[str] = None) -> dict[str, Any]:
    """
    Маскирует чувствительные значения в словаре по ключам.
    
    Args:
        data: Словарь для обработки
        sensitive_keys: Набор ключей, значения которых нужно маскировать
    
    Returns:
        Новый словарь с замаскированными значениями
    """
    if sensitive_keys is None:
        sensitive_keys = {
            'password', 'token', 'secret', 'access_token', 'refresh_token',
            'authorization', 'api_key', 'secret_key', 'private_key', 'email'
        }
    
    result = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Если ключ чувствительный - маскируем
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            if 'email' in key_lower:
                result[key] = mask_email(str(value)) if value else value
            elif any(word in key_lower for word in ['password', 'secret', 'key']):
                result[key] = mask_password(str(value)) if value else value
            elif 'token' in key_lower:
                result[key] = mask_token(str(value)) if value else value
            else:
                result[key] = "***REDACTED***"
        # Если значение - словарь, рекурсивно обрабатываем
        elif isinstance(value, dict):
            result[key] = mask_dict_values(value, sensitive_keys)
        # Если значение - список словарей, обрабатываем каждый элемент
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            result[key] = [mask_dict_values(item, sensitive_keys) if isinstance(item, dict) else item for item in value]
        else:
            result[key] = value
    
    return result

