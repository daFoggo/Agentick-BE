import os
from enum import Enum
from pathlib import Path
from typing import List

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Environment(str, Enum):
    PROD = "prod"
    STAGE = "stage"
    DEV = "dev"
    TEST = "test"


def _get_env_files() -> List[str]:
    """
    Helper to determine environment files to load.
    Prioritizes .env first, then overrides with .env.{ENV} if it exists.
    """
    current_env = os.getenv("ENV", "dev")
    potential_files = [".env", f".env.{current_env}"]
    existing_files = []
    for filename in potential_files:
        file_path = PROJECT_ROOT / filename
        if file_path.exists():
            existing_files.append(str(file_path))
    return existing_files


class Settings(BaseSettings):
    # base
    APP_NAME: str = "agentick-be"
    PROJECT_NAME: str = "fca-api"
    ENV: Environment = Environment.DEV
    TIMEZONE: str = "Asia/Ho_Chi_Minh"
    API: str = "/api"
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    PROJECT_ROOT: str = str(PROJECT_ROOT)

    ENV_DATABASE_MAPPER: dict[str, str] = Field(
        default_factory=lambda: {
            "prod": "fca",
            "stage": "stage-fca",
            "dev": "dev-fca",
            "test": "test-fca",
        }
    )
    DB_ENGINE_MAPPER: dict[str, str] = Field(
        default_factory=lambda: {
            "postgresql": "postgresql",
            "mysql": "mysql+pymysql",
        }
    )

    # date
    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%S"
    DATE_FORMAT: str = "%Y-%m-%d"

    # auth
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    # database
    DB: str = "postgresql"
    DB_USER: str | None = None
    DB_PASSWORD: str | None = None
    DB_HOST: str | None = None
    DB_PORT: str = "3306"
    DATABASE_URL: str | None = None

    DATABASE_URI_FORMAT: str = (
        "{db_engine}://{user}:{password}@{host}:{port}/{database}"
    )

    # Email / SMTP configuration
    SMTP_HOST: str | None = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_NAME: str = "Agentick"

    FRONTEND_URL: str = "http://localhost:3000"

    # OpenRouter
    OPENROUTER_API_KEY: str | None = None
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"

    # Telegram Configuration
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    # find query
    PAGE: int = 1
    PAGE_SIZE: int = 20
    ORDERING: str = "-id"

    model_config = SettingsConfigDict(
        env_file=_get_env_files(),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @computed_field(return_type=str)
    @property
    def DB_ENGINE(self) -> str:
        return self.DB_ENGINE_MAPPER.get(self.DB, "postgresql")

    @property
    def is_production(self) -> bool:
        return self.ENV == Environment.PROD

    @property
    def is_development(self) -> bool:
        return self.ENV == Environment.DEV

    @property
    def is_testing(self) -> bool:
        return self.ENV == Environment.TEST

    @computed_field(return_type=str)
    @property
    def DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        database = self.ENV_DATABASE_MAPPER.get(
            self.ENV, self.ENV_DATABASE_MAPPER["dev"]
        )
        missing_values = [
            name
            for name, value in {
                "DB_USER": self.DB_USER,
                "DB_PASSWORD": self.DB_PASSWORD,
                "DB_HOST": self.DB_HOST,
            }.items()
            if not value
        ]
        if missing_values:
            missing = ", ".join(missing_values)
            raise ValueError(
                f"Missing database configuration: {missing}. Set DATABASE_URL or provide DB_* fields."
            )

        return self.DATABASE_URI_FORMAT.format(
            db_engine=self.DB_ENGINE,
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=database,
        )


class TestSettings(Settings):
    ENV: Environment = Environment.TEST


settings: Settings = TestSettings() if os.getenv("ENV", "dev") == "test" else Settings()
configs = settings
