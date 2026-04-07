from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "agentick-be"
    ENV: str = "dev"
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@db:5432/agentick_be"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
