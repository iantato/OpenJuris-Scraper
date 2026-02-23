from typing import Optional
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

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Generate a chat completion response.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text response

        Note: This is optional - subclasses that support text generation should override this.
        """
        raise NotImplementedError("This embedder does not support chat completion")