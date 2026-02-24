from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScraperSettings(BaseSettings):
    """Configuration for scraper behavior"""

    # Rate limiting
    requests_per_second: float = Field(default=0.5, alias="SCRAPER_REQUESTS_PER_SECOND")
    max_concurrent_requests: int = Field(default=5, alias="SCRAPER_MAX_CONCURRENT_REQUESTS")
    request_timeout: int = Field(default=30, alias="SCRAPER_REQUEST_TIMEOUT")

    # Retry behavior
    max_retries: int = Field(default=3, alias="SCRAPER_MAX_RETRIES")
    retry_backoff_base: float = Field(default=2.0, alias="SCRAPER_RETRY_BACKOFF_BASE")

    # User Agent
    user_agent: str = "OpenJuris-Scraper (PH Legal Documents Archive); cmfrancisco.business@gmail.com"

    # Storage
    save_raw_html: bool = Field(default=True, alias="SCRAPER_SAVE_RAW_HTML")
    raw_html_dir: Optional[str] = Field(default=None, alias="SCRAPER_RAW_HTML_DIR")

    # Limits
    max_documents_per_run: Optional[int] = Field(default=None, alias="SCRAPER_MAX_DOCUMENTS_PER_RUN")
    max_depth: int = 3

    # Rate limit in seconds between requests (used by HttpClient)
    rate_limit: float = Field(default=1.0, alias="SCRAPER_RATE_LIMIT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore"
    )