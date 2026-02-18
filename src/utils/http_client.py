import asyncio
from typing import Optional

import aiohttp

from config.scraper import ScraperSettings

from exceptions import ScraperException

class HTTPClient:
    """Async HTTP client with rate limiting and retry logic"""

    def __init__(self, config: ScraperSettings):
        self.config = config
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_requests)    # Limits concurrent requests
        self._last_request_time = 0.0       # Tracks when the last request was made
        self._lock = asyncio.Lock()         # Prevents race conditions when checking rate limit
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session (lazy initialization)"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.config.request_timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": self.config.user_agent
                }
            )
        return self._session

    async def _rate_limit(self):
        """Enforce rate limiting between requests"""
        async with self._lock:
            loop = asyncio.get_event_loop()
            current_time = loop.time()
            min_interval = 1.0 / self.config.requests_per_second
            elapsed = current_time - self._last_request_time

            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

            self._last_request_time = loop.time()

    async def get(self, url: str, retries: Optional[int] = None) -> str:
        """Fetch URL with rate limiting and retry logic"""
        retries = retries or self.config.max_retries

        async with self._semaphore:
            await self._rate_limit()

            session = await self._get_session()
            last_error: Optional[Exception] = None

            for attempt in range(retries):
                try:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        return await response.text()
                except aiohttp.ClientError as e:
                    last_error = e
                    if attempt < retries - 1:
                        wait_time = self.config.retry_backoff_base ** attempt
                        await asyncio.sleep(wait_time)
                    continue

            raise last_error or ScraperException(f"Failed to fetch {url}")

    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        """Asynchronous context manager entry"""
        return self

    async def __aexit__(self, *args):
        """Asynchronous context manager exit"""
        await self.close()