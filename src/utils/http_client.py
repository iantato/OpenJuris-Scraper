import asyncio
import random
import time
from typing import Optional

import httpx
from loguru import logger


class HttpClient:
    """Async HTTP client with rate limiting and retries."""

    def __init__(
        self,
        rate_limit: float = 1.0,
        request_timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str = "OpenJuris-Scraper/1.0",
    ):
        self.rate_limit = rate_limit
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self._client: Optional[httpx.AsyncClient] = None
        self._last_request_time: float = 0

    async def start(self):
        """Initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.request_timeout),
                follow_redirects=True,
                headers={
                    "User-Agent": self.user_agent
                }
            )
            logger.debug("HTTP client started")

    async def close(self):
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("HTTP client closed")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _rate_limit_wait(self):
        """Wait to respect rate limiting with jitter."""
        now = time.time()
        elapsed = now - self._last_request_time
        target = self.rate_limit

        # Add +/-20% jitter to avoid thundering herd
        jitter = target * 0.2
        wait_for = max(0, target + random.uniform(-jitter, jitter) - elapsed)

        if wait_for > 0:
            await asyncio.sleep(wait_for)

        self._last_request_time = time.time()

    async def get_bytes(self, url: str) -> bytes:
        """Fetch URL and return response bytes."""
        if self._client is None:
            await self.start()

        await self._rate_limit_wait()

        for attempt in range(self.max_retries):
            try:
                response = await self._client.get(url)
                response.raise_for_status()
                return response.content
            except httpx.HTTPStatusError as e:
                logger.warning(f"HTTP error {e.response.status_code} for {url}, attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                logger.warning(f"Request error for {url}: {e}, attempt {attempt + 1}/{self.max_retries}")
                if attempt == self.max_retries - 1:
                    raise
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} attempts")

    async def get_text(self, url: str) -> str:
        """Fetch URL and return response text."""
        content = await self.get_bytes(url)
        return content.decode('utf-8', errors='replace')