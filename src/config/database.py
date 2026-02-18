from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

class DatabaseSettings(BaseSettings):
    """
    Dedicated settings for Database connections.
    """

    # Standard Database Parameters
    database_url: str
    turso_auth_token: Optional[str] = None

    # Config to read from .env
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")