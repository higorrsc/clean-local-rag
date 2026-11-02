from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    """

    # Database configuration
    pg_dsn: str = "postgresql://dev:dev@localhost:5432/rag_db"
    vector_backend: Literal["memory", "pgvector"] = "memory"

    # Ollama configuration
    ollama_base_url: str = "http://localhost:11434/api"
    embed_model: str = "nomic-embed-text:latest"
    chat_model: str = "qwen3:4b-instruct"
    ollama_timeout: float = 180.0

    # Configuration for reading the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Global instance to be imported and injected where necessary
settings = Settings()
