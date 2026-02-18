from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.enums.app_environment import AppEnvironment

from src.config.database import DatabaseSettings

class Settings(DatabaseSettings):
    """
    Main Application Settings.
    """
    app_name: str = "OpenJuris API | Legal Documents Archive"
    environment: AppEnvironment = AppEnvironment.PRODUCTION

    # --- External APIs ---
    LLM_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == AppEnvironment.PRODUCTION

settings = Settings()