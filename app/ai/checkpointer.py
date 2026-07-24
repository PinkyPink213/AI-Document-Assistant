from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool


def to_psycopg_connection_string(database_url: str) -> str:
    """Convert a SQLAlchemy PostgreSQL URL into a psycopg connection URL."""
    return database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    ).replace(
        "postgresql+psycopg2://",
        "postgresql://",
        1,
    )


@asynccontextmanager
async def postgres_checkpointer(
    database_url: str,
) -> AsyncIterator[AsyncPostgresSaver]:
    connection_string = to_psycopg_connection_string(database_url)
    pool = AsyncConnectionPool(
        conninfo=connection_string,
        min_size=1,
        max_size=5,
        open=False,
        check=AsyncConnectionPool.check_connection,
        max_idle=300,
        max_lifetime=1800,
        reconnect_timeout=30,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
        },
    )
    async with pool:
        checkpointer = AsyncPostgresSaver(pool)
        await checkpointer.setup()
        yield checkpointer
