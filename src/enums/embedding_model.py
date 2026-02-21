from enum import Enum

class EmbeddingModel(str, Enum):
    DEFAULT = "BAAI/bge-small-en-v1.5"

    # Ollama Embedding Models.
    BGE_SMALL = "bge-small"
    NOMIC = "nomic-embed-text"
    MXBAI = "mxbai-embed-large"

    # Voyager Embedding Models.
    VOYAGE = "voyage-law-2"