"""
Конфигурация для тестов.
"""

import warnings

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies.database import get_database
from app.core.auth import hash_password
from app.core.database import Base, get_db
from app.main import app
from app.models.user import User

# Подавляем warnings из внешних библиотек
warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.*")
warnings.filterwarnings("ignore", message=".*utcnow.*")


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


# Переопределяем обе зависимости
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_database] = override_get_db


@pytest.fixture(scope="session")
def test_engine():
    """Фикстура для тестового движка БД."""
    return engine


@pytest.fixture(scope="function")
def db_session():
    """Фикстура для тестовой сессии БД."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client():
    """Фикстура для тестового клиента."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_user(db_session):
    """Фикстура для тестового пользователя."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=hash_password("testpassword"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    """Фикстура для заголовков авторизации."""
    from app.core.auth import create_access_token

    # Создаем токен напрямую
    token_data = {"sub": str(test_user.id), "username": test_user.username}
    token = create_access_token(token_data)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def multiple_users(db_session):
    """Фикстура для нескольких тестовых пользователей."""
    users = []
    for i in range(3):
        user = User(
            username=f"user{i+1}",
            email=f"user{i+1}@example.com",
            hashed_password=hash_password("password123"),
        )
        db_session.add(user)
        users.append(user)

    db_session.commit()
    for user in users:
        db_session.refresh(user)

    return users


@pytest.fixture(scope="function")
def test_wishes(db_session, test_user):
    """Фикстура для тестовых желаний."""
    from app.models.wish import Wish

    wishes = []
    wish_titles = [
        "Купить новый ноутбук",
        "Изучить Python",
        "Путешествие в Японию",
        "Купить велосипед",
        "Изучить машинное обучение",
    ]

    for title in wish_titles:
        wish = Wish(
            title=title,
            description=f"Описание для {title}",
            user_id=test_user.id,
        )
        db_session.add(wish)
        wishes.append(wish)

    db_session.commit()
    for wish in wishes:
        db_session.refresh(wish)

    return wishes


@pytest.fixture(autouse=True)
def clean_database():
    """Автоматическая очистка БД после каждого теста."""
    yield
    # Очистка происходит в db_session фикстуре
    pass


@pytest.fixture(autouse=True)
def clean_rate_limiter():
    """Автоматическая очистка rate limiter перед каждым тестом."""
    # Очищаем глобальное состояние rate limiter перед тестом
    from app.middleware.rate_limiting import clear_rate_limiter_state

    clear_rate_limiter_state()
    yield


# настройки для pytest
def pytest_configure(config):
    """Конфигурация pytest."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "nfr: mark test as NFR test")
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line(
        "markers", "reliability: mark test as reliability test"
    )
    config.addinivalue_line(
        "markers", "scalability: mark test as scalability test"
    )
    config.addinivalue_line(
        "markers", "benchmark: mark test as benchmark test"
    )

    # подавляем warnings из библиотек (а то спамят в консоль)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings(
        "ignore", category=pytest.PytestReturnNotNoneWarning
    )


def pytest_collection_modifyitems(config, items):
    """Модификация коллекции тестов."""
    for item in items:
        # автоматом помечаем тесты по их расположению
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in item.nodeid:
            item.add_marker(pytest.mark.e2e)
            item.add_marker(pytest.mark.slow)
        elif "nfr" in item.nodeid:
            item.add_marker(pytest.mark.nfr)
            # добавляем специфичные маркеры для NFR тестов
            if "test_performance" in item.nodeid:
                item.add_marker(pytest.mark.performance)
            if "test_security" in item.nodeid:
                item.add_marker(pytest.mark.security)
            if "test_reliability" in item.nodeid:
                item.add_marker(pytest.mark.reliability)
            if "test_scalability" in item.nodeid:
                item.add_marker(pytest.mark.scalability)
