from pydantic import computed_field
from pydantic_settings import SettingsConfigDict

from enums.app_environment import AppEnvironment

from config.scraper import ScraperSettings
from config.database import DatabaseSettings
from config.embedder import EmbedderSettings

class Settings(DatabaseSettings, ScraperSettings, EmbedderSettings):
    """
    Main Application Settings.
    """
    app_name: str = "OpenJuris API | Legal Documents Archive"
    environment: AppEnvironment = AppEnvironment.PRODUCTION

    internal_api_key: str

    # --- External APIs ---
    llm_api_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == AppEnvironment.PRODUCTION