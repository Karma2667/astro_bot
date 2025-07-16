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


db_query_logger.info("Database URL: %s", settings.database.DATABASE_URL)
engine = create_async_engine(
      settings.database.DATABASE_URL,
      echo=False,
      future=True,
)
# engine = create_engine(settings.database.DATABASE_URL)
async_session_maker = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
session_maker = sessionmaker(engine, expire_on_commit=False)


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
    db_query_logger.debug("Start Query:\n%s" % statement)
    db_query_logger.debug("Parameters:\n%r" % (parameters,))


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
    db_query_logger.debug("Query Complete!\n\n")
    db_query_logger.debug("Total Time: %.02fms" % (total * 1000))