"""
Configuration Management

Type-safe configuration via pydantic-settings. Every environment variable is
validated on first access, so a missing credential fails at startup rather than
on the first request that needs it.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root, from cv_matching/src/infrastructure/config/settings.py
_ENV_FILE = str(Path(__file__).resolve().parents[4] / ".env")


class AzureDocumentIntelligenceSettings(BaseSettings):
    """Azure Document Intelligence configuration, used to OCR the uploaded CV."""

    endpoint: str = Field(..., alias="AZURE__ENDPOINT")
    region: str = Field(default="japaneast", alias="AZURE__REGION")
    key: str = Field(..., alias="AZURE__KEY")

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class LiteLLMSettings(BaseSettings):
    url: str = Field(..., alias="CV_MATCHING_LITELLM__URL")
    api_key: str = Field(..., alias="CV_MATCHING_LITELLM__API_KEY")
    model: str = Field(default="gemini-3.1-flash-lite-preview", alias="CV_MATCHING_LITELLM__MODEL")
    # Under the proxy's 120s Cloudflare read timeout, so a slow call fails as our
    # timeout - which max_retries can act on - rather than as an opaque 524.
    timeout: int = Field(default=90, alias="CV_MATCHING_LITELLM__TIMEOUT")
    max_retries: int = Field(default=2, ge=0, le=5, alias="CV_MATCHING_LITELLM__MAX_RETRIES")
    reasoning_effort: Optional[str] = Field(
        default=None, alias="CV_MATCHING_LITELLM__REASONING_EFFORT"
    )

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AuthenticationSettings(BaseSettings):
    """API authentication configuration."""

    api_key: str = Field(..., alias="AUTH__API_KEY")

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class AppSettings(BaseSettings):
    """Application-wide settings.

    The path defaults reproduce the routes this service had while it was mounted
    inside the unified API, so clients keep working unchanged after the split.
    `root_path` is what sits in front of the app at the ingress; the app itself
    serves `/cv-matching/...`.
    """

    app_name: str = Field(default="CV Matching API", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    root_path: str = Field(default="/ai", alias="ROOT_PATH")
    service_prefix: str = Field(default="/cv-matching", alias="SERVICE_PREFIX")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    allowed_origins: list[str] = Field(default=["*"], alias="ALLOWED_ORIGINS")

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


class CvMatchingSettings:
    """Unified settings container."""

    def __init__(self):
        self.app = AppSettings()
        self.azure = AzureDocumentIntelligenceSettings()
        self.litellm = LiteLLMSettings()
        self.authentication = AuthenticationSettings()


_settings: Optional[CvMatchingSettings] = None


def get_cv_matching_settings() -> CvMatchingSettings:
    global _settings
    if _settings is None:
        _settings = CvMatchingSettings()
    return _settings
