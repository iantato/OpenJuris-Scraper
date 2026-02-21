from embedder.providers.base import BaseEmbedder

from config.embedder import EmbedderSettings

class OllamaEmbedder(BaseEmbedder):

    def __init__(self, settings: EmbedderSettings):
        super().__init__(settings)

    @property
    def dimension(self) -> int:
        """Return the embedding dimension"""
        return self.settings.embedding_dimension

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        pass