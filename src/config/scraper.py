from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class ScraperSettings(BaseSettings):
    """Configuration for scraper behavior"""

    # Rate limiting
    requests_per_second: float = 2.0    # Max requests per second
    max_concurrent_requests: int = 5    # Max parallel requests
    request_timeout: int = 30           # Timeout in seconds

    # Retry behavior
    max_retries: int = 3
    retry_backoff_base: float = 2.0     # Exponential backoff base

    # User Agent
    user_agent: str = "OpenJuris-Scraper (PH Legal Documents Archive); cmfrancisco.business@gmail.com"

    # Storage
    save_raw_html: bool = True          # Keep raw HTML for debugging
    raw_html_dir: Optional[str]         # Directory for raw HTML files

    # Limits
    max_documents_per_run: Optional[int] = None # None = unlimited
    max_depth: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SCRAPER_",
        env_ignore_empty=True,
        extra="ignore"
    )