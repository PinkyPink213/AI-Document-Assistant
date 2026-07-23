from contextlib import asynccontextmanager
from typing import AsyncIterator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


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
    async with AsyncPostgresSaver.from_conn_string(
        connection_string,
    ) as checkpointer:
        await checkpointer.setup()
        yield checkpointer
