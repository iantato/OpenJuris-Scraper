from typing import List, Optional

import httpx

from config import Settings
from embedder.providers.base import BaseEmbedder

class OllamaEmbedder(BaseEmbedder):
    def __init__(self, settings: Settings):
        self.base_url = settings.ollama_host
        self.embedding_model = settings.ollama_model
        self.chat_model = getattr(settings, 'ollama_chat_model', settings.ollama_model)

    async def embed(self, text: str) -> List[float]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            return response.json()["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings

    async def chat_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3
    ) -> str:
        """
        Generate a chat completion response using Ollama.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0-1)

        Returns:
            Generated text response
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": self.chat_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            return response.json().get("response", "")