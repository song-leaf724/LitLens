from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Literature Deep Reading Assistant"
    debug: bool = True

    database_url: str = "sqlite:///./data/app.db"
    upload_dir: str = "./data/uploads"
    chroma_persist_dir: str = "./data/chroma"
    chroma_collection_name: str = "literature_chunks"
    book_source_proxy: Optional[str] = None

    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: Optional[str] = None
    llm_model_name: str = "gpt-4o-mini"
    embedding_model_name: str = "text-embedding-3-small"
    embedding_batch_size: int = Field(default=16, ge=1, le=128)
    llm_timeout_seconds: int = 60
    llm_use_fake: bool = False

    chunk_size: int = Field(default=900, ge=200)
    chunk_overlap: int = Field(default=150, ge=0)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)
    max_context_chars: int = Field(default=6000, ge=1000)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

