from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()