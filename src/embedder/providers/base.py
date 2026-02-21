from abc import ABC, abstractmethod

from config.embedder import EmbedderSettings

class BaseEmbedder(ABC):
    """Base class for embedding services."""

    def __init__(self, settings: EmbedderSettings):
        self.settings = settings

    @property
    @abstractmethod
    def dimensions(self) -> int:
        ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        ...

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...