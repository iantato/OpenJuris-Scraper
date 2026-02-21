import asyncio

from sentence_transformers import SentenceTransformer

from embedder.providers.base import BaseEmbedder

from config.embedder import EmbedderSettings

class BGESmallEmbedder(BaseEmbedder):
    def __init__(self, settings: EmbedderSettings):
        super().__init__(settings)
        self.batch_size = settings.batch_size

        self._model = SentenceTransformer(
            self.settings.embedding_model.value,
            device="cuda"
        )

        self.settings.embedding_dimension = self._model.get_sentence_embedding_dimension()

    @property
    def dimensions(self) -> int:
        return self._model.get_sentence_embedding_dimension()

    async def embed(self, text: str) -> list[float]:
        """Embeds a single string non-blockingly"""
        vector = await asyncio.to_thread(self._model.encode, text)
        return vector.tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embeds a list of strings efficiently in batches"""
        if not texts:
            return []

        vectors = await asyncio.to_thread(
            self._model.encode,
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
        )

        return vectors.tolist()