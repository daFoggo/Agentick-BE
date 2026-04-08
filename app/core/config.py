from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "agentick-be"
    ENV: str = "dev"
    # Require DATABASE_URL from environment to avoid shipping credentials in code.
    DATABASE_URL: str = Field(...)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
