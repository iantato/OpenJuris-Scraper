from config.embedder import EmbedderSettings
from enums.embedding_provider import EmbeddingProvider
from embedder.providers.base import BaseEmbedder
from embedder.providers.bge_small import BGESmallEmbedder
from embedder.providers.ollama import OllamaEmbedder


def get_embedder(settings: EmbedderSettings) -> BaseEmbedder:
    """
    Factory function to create the appropriate embedder based on settings.

    If no provider is specified, defaults to BGESmallEmbedder (local).
    """
    provider = settings.embedding_provider

    if provider is None:
        # Default to local BGE Small embedder
        return BGESmallEmbedder(settings)

    if provider == EmbeddingProvider.OLLAMA:
        return OllamaEmbedder(settings)

    # if provider == EmbeddingProvider.OPENAI:
    #     return OpenAIEmbedder(settings)
    # if provider == EmbeddingProvider.VOYAGE:
    #     return VoyageEmbedder(settings)

    # Fallback to BGE Small
    return BGESmallEmbedder(settings)