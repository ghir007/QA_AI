from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Agentic QA Copilot"
    artifact_root: Path = Field(default=Path("artifacts/runs"), alias="ARTIFACT_ROOT")
    sample_sut_base_url: str = Field(default="http://127.0.0.1:8010", alias="SAMPLE_SUT_BASE_URL")
    browser_executor: str = Field(default="none", alias="BROWSER_EXECUTOR")
    browser_fake_outcome: str = Field(default="passed", alias="BROWSER_FAKE_OUTCOME")
    mcp_browser_endpoint: str | None = Field(default=None, alias="MCP_BROWSER_ENDPOINT")
    mcp_browser_timeout_seconds: float = Field(default=5.0, alias="MCP_BROWSER_TIMEOUT_SECONDS")


def get_settings() -> Settings:
    settings = Settings()
    settings.artifact_root = settings.artifact_root.resolve()
    return settings