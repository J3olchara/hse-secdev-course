#!/usr/bin/env python3
"""
Скрипт для генерации криптографически стойких секретов (ADR-003)
"""
import secrets


def generate_secret_key(length: int = 32) -> str:
    """
    Генерирует криптографически стойкий SECRET_KEY
    
    Args:
        length: Длина в байтах (32 байта = 256 бит)
    
    Returns:
        URL-safe строка секрета
    """
    return secrets.token_urlsafe(length)


def main():
    print("=" * 60)
    print("Генератор секретов для Wishlist API (ADR-003)")
    print("=" * 60)
    print()
    
    # JWT Secret Key
    secret_key = generate_secret_key(32)
    print("SECRET_KEY (для JWT подписи):")
    print(secret_key)
    print()
    
    # Для ротации - генерируем второй ключ
    print("SECRET_KEY для ротации (опционально):")
    secret_key_2 = generate_secret_key(32)
    print(secret_key_2)
    print()
    
    print("-" * 60)
    print("Добавьте эти переменные в ваш .env файл:")
    print("-" * 60)
    print()
    print("# JWT Secrets")
    print(f"SECRET_KEY={secret_key}")
    print(f"# SECRET_KEY_PREVIOUS={secret_key_2}")
    print()
    print("⚠️  ВАЖНО:")
    print("1. НЕ коммитьте .env файл в git!")
    print("2. Используйте разные ключи для dev/staging/production")
    print("3. Ротируйте секреты каждые 30 дней (NFR-05)")
    print("4. Храните backup ключей в безопасном месте")
    print()


if __name__ == "__main__":
    main()

