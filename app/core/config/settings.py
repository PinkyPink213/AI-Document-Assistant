from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins(value: str) -> list[str]:
    return [
        origin.strip().rstrip("/")
        for origin in value.split(",")
        if origin.strip()
    ]


class Settings(BaseSettings):
    openai_api_key: str
    openai_embeddings_model: str
    openai_chat_model: str
    qdrant_url: str
    qdrant_api_key: str
    postgres_url: str
    qdrant_collection_name: str 
    langsmith_api_key: str
    langsmith_project: str
    langsmith_endpoint: str
    langsmith_tracing: str
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = 60
    rate_limit_default_requests: int = 120
    rate_limit_chat_requests: int = 30
    rate_limit_upload_requests: int = 10
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return parse_cors_origins(self.cors_origins)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
