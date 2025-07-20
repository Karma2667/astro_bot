from time import time
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.engine import Engine
from sqlalchemy.engine import Connection
from sqlalchemy.engine.interfaces import DBAPICursor, _DBAPIAnyExecuteParams
from sqlalchemy.engine.interfaces import ExecutionContext

from config import settings
from logger import db_query_logger
from database.base import Base  # Импортируем Base для создания таблиц

# Логирование URL базы данных
db_query_logger.info("Database URL: %s", settings.database.DATABASE_URL)

# Создание асинхронного движка
engine = create_async_engine(
    settings.database.DATABASE_URL,
    echo=False,
    future=True,
)

# Асинхронный создатель сессий
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Синхронный создатель сессий (оставлен для совместимости, но не используется)
session_maker = sessionmaker(engine, expire_on_commit=False)

# Функция инициализации базы данных
async def init_db():
    """Initialize the database by creating all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(bind=sync_conn))
        db_query_logger.info("Database tables created successfully")

# Обработчики событий для логирования запросов
@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(
    conn: Connection,
    cursor: DBAPICursor,
    statement: str,
    parameters: _DBAPIAnyExecuteParams,
    context: ExecutionContext | None,
    executemany: bool,
) -> None:
    context._query_start_time = time()
    db_query_logger.debug("Start Query:\n%s", statement)
    db_query_logger.debug("Parameters:\n%r", parameters)

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(
    conn: Connection,
    cursor: DBAPICursor,
    statement: str,
    parameters: _DBAPIAnyExecuteParams,
    context: ExecutionContext,
    executemany: bool,
) -> None:
    total = time() - context._query_start_time
    db_query_logger.debug("Query Complete!\n")
    db_query_logger.debug("Total Time: %.02fms", total * 1000)