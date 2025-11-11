import logging

from .core.database import Base, create_tables, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    try:
        logger.info("Создание таблиц в базе данных...")
        create_tables()
        logger.info("Таблицы успешно созданы!")
    except Exception as e:
        logger.error(f"Ошибка при создании таблиц: {e}")
        raise


def reset_database():
    try:
        logger.warning("Удаление всех таблиц...")
        Base.metadata.drop_all(bind=engine)
        logger.info("Таблицы удалены.")

        logger.info("Создание таблиц заново...")
        create_tables()
        logger.info("База данных сброшена и пересоздана!")
    except Exception as e:
        logger.error(f"Ошибка при сбросе базы данных: {e}")
        raise


if __name__ == "__main__":
    init_database()
