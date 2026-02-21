from enum import Enum

class EmbeddingProvider(str, Enum):
    OLLAMA = "Ollama"
    OPENAI = "OpenAI"
    VOYAGE = "Voyage"