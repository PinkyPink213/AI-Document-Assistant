from app.core.config.settings import parse_cors_origins


def test_parses_and_normalizes_cors_origins():
    assert parse_cors_origins(
        "http://localhost:3000/, "
        "https://assistant.vercel.app, ,"
    ) == [
        "http://localhost:3000",
        "https://assistant.vercel.app",
    ]
