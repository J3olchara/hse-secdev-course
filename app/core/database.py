import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Определяем тип БД на основе окружения
STAGE = os.getenv("STAGE", "local")
DATABASE_URL_ENV = os.getenv("DATABASE_URL")

# Если DATABASE_URL установлена (Docker) или STAGE=production → PostgreSQL
# Иначе → SQLite для локальной разработки
if DATABASE_URL_ENV:
    DATABASE_URL = DATABASE_URL_ENV
elif STAGE == "production":
    DATABASE_URL = "postgresql+psycopg://wishlist_user:wishlist_password@localhost:5432/wishlist_db"
else:
    # SQLite для локальной разработки
    DATABASE_URL = "sqlite:///./test.db"

# Для SQLite нужен connect_args
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
