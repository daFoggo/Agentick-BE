import os
from pathlib import Path

from pydantic import Field, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # base
    APP_NAME: str = "agentick-be"
    PROJECT_NAME: str = "fca-api"
    ENV: str = "dev"
    API: str = "/api"
    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    PROJECT_ROOT: str = str(Path(__file__).resolve().parents[2])

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

    DATABASE_URI_FORMAT: str = "{db_engine}://{user}:{password}@{host}:{port}/{database}"

    # find query
    PAGE: int = 1
    PAGE_SIZE: int = 20
    ORDERING: str = "-id"

    model_config = SettingsConfigDict(
        env_file=".env",
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

    @computed_field(return_type=str)
    @property
    def DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        database = self.ENV_DATABASE_MAPPER.get(self.ENV, self.ENV_DATABASE_MAPPER["dev"])
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
    ENV: str = "test"


settings: Settings = TestSettings() if os.getenv("ENV", "dev") == "test" else Settings()
configs = settings
