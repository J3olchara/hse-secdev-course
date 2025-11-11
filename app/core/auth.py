from datetime import datetime, timedelta, timezone
from typing import Optional

import argon2
from jose import JWTError, jwt

from .config import settings
from .exceptions import UnauthorizedError

# Используем Argon2id для более сильного хеширования паролей
# Параметры: time_cost=3, memory_cost=256*1024, parallelism=1 (как указано в NFR-01)
ph = argon2.PasswordHasher(
    time_cost=3,
    memory_cost=256 * 1024,  # 256 MB
    parallelism=1,
    hash_len=32,
    salt_len=16,
    encoding="utf-8",
)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise UnauthorizedError("Invalid token")


def get_user_id_from_token(token: str) -> int:
    payload = verify_token(token)
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise UnauthorizedError("Token does not contain user ID")
    try:
        return int(user_id_str)
    except ValueError:
        raise UnauthorizedError("Invalid user ID in token")


def get_username_from_token(token: str) -> str:
    payload = verify_token(token)
    username: str = payload.get("username")
    if username is None:
        raise UnauthorizedError("Token does not contain username")
    return username


def hash_password(password: str) -> str:
    """Хеширует пароль с использованием Argon2id согласно NFR-01"""
    if len(password) > 72:
        password = password[:72]
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль с использованием Argon2id согласно NFR-01"""
    try:
        ph.verify(hashed_password, plain_password)
        return True
    except argon2.exceptions.VerifyMismatchError:
        return False
    except argon2.exceptions.InvalidHash:
        # Fallback для старых pbkdf2 хешей (для обратной совместимости)
        from passlib.context import CryptContext

        pwd_context = CryptContext(
            schemes=["pbkdf2_sha256"], deprecated="auto"
        )
        return pwd_context.verify(plain_password, hashed_password)
