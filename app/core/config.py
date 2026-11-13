"""Application configuration loaded from YAML and environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


class ModelSettings(BaseModel):
    """Local model configuration."""

    chat: str
    chat_secondary: str | None = None
    embedding: str
    temperature: float


class OllamaSettings(BaseModel):
    """Ollama server configuration."""

    base_url: str


class DatabaseSettings(BaseModel):
    """Database connection configuration."""

    url: str


class ChromaSettings(BaseModel):
    """Chroma persistence configuration."""

    path: str


class CorsSettings(BaseModel):
    """Allowed browser origins for the API."""

    origins: list[str]


class Settings(BaseSettings):
    """ShopAssist settings with environment overrides for YAML values."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    models: ModelSettings
    ollama: OllamaSettings
    database: DatabaseSettings
    chroma: ChromaSettings
    cors: CorsSettings

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Load YAML defaults before environment-based overrides."""

        yaml_settings = YamlConfigSettingsSource(
            settings_cls,
            yaml_file=CONFIG_PATH,
            yaml_file_encoding="utf-8",
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_settings,
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()


__all__: tuple[str, ...] = ["CONFIG_PATH", "Settings", "get_settings"]
