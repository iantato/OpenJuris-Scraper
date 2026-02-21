from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from enums.embedding_model import EmbeddingModel
from enums.embedding_provider import EmbeddingProvider

class EmbedderSettings(BaseSettings):
    embedding_provider: Optional[EmbeddingProvider] = Field(default=None, alias="EMBEDDING_PROVIDER")
    embedding_model: EmbeddingModel = Field(default=None, alias="EMBEDDING_MODEL")
    embedding_dimension: Optional[int] = Field(default=None, alias="EMBEDDING_DIMENSION")

    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    voyager_api_key: Optional[str] = Field(default=None, alias="VOYAGER_API_KEY")

    ollama_base_url: Optional[str] = Field(default=None, alias="OLLAMA_URL")

    chunk_size: int = 512
    overlap: int = 200

    batch_size: int = 30

    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )