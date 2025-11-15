import os
from typing import Optional


class Settings:
    """
    Настройки приложения с безопасным управлением секретами (ADR-003)
    """

    # Database settings
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "wishlist_user")
    POSTGRES_PASSWORD: str = os.getenv(
        "POSTGRES_PASSWORD", "wishlist_password"
    )
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "wishlist_db")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # JWT секреты - поддержка ротации (ADR-003, NFR-05)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    SECRET_KEY_PREVIOUS: Optional[str] = os.getenv("SECRET_KEY_PREVIOUS")

    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )

    # Environment
    STAGE: str = os.getenv("STAGE", "local")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Rate limiting (ADR-002)
    RATE_LIMIT_ENABLED: bool = (
        os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    )

    def __post_init__(self):
        """Валидация секретов при старте (ADR-003)"""
        # Проверяем что SECRET_KEY установлен
        if not self.SECRET_KEY:
            # В local режиме используем дефолтный ключ с warning
            if self.STAGE == "local":
                self.SECRET_KEY = "dev-secret-key-DO-NOT-USE-IN-PRODUCTION"
                print(
                    "WARNING: Using default SECRET_KEY for local development. Set SECRET_KEY env var!"
                )
            else:
                raise ValueError(
                    "SECRET_KEY environment variable must be set in production!"
                )

        # Проверяем что не используется дефолтный пароль в production
        if self.STAGE == "production":
            dangerous_patterns = [
                "change-in-production",
                "your-secret",
                "dev-secret",
            ]
            if any(
                pattern in self.SECRET_KEY.lower()
                for pattern in dangerous_patterns
            ):
                raise ValueError(
                    "Default SECRET_KEY detected in production! This is insecure!"
                )

            # Проверка минимальной длины ключа (ADR-003)
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters long!"
                )


settings = Settings()

# Валидация при импорте
if hasattr(settings, '__post_init__'):
    settings.__post_init__()
