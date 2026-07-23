from app.ai.checkpointer import to_psycopg_connection_string


def test_converts_sqlalchemy_psycopg_url_for_langgraph():
    assert (
        to_psycopg_connection_string(
            "postgresql+psycopg://user:password@localhost:5432/app"
        )
        == "postgresql://user:password@localhost:5432/app"
    )


def test_converts_sqlalchemy_psycopg2_url_for_langgraph():
    assert (
        to_psycopg_connection_string(
            "postgresql+psycopg2://user:password@localhost:5432/app"
        )
        == "postgresql://user:password@localhost:5432/app"
    )
