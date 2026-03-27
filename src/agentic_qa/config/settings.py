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
    mcp_browser_command: str | None = Field(default=None, alias="MCP_BROWSER_COMMAND")
    mcp_browser_args_json: str = Field(default="[]", alias="MCP_BROWSER_ARGS_JSON")
    mcp_browser_tool_name: str = Field(default="browser_validate_ui", alias="MCP_BROWSER_TOOL_NAME")
    mcp_browser_timeout_seconds: float = Field(default=5.0, alias="MCP_BROWSER_TIMEOUT_SECONDS")
    enable_rag_context: bool = Field(default=False, alias="ENABLE_RAG_CONTEXT")
    rag_source_root: Path = Field(default=Path("docs/rag-seeds"), alias="RAG_SOURCE_ROOT")
    rag_vector_store_path: Path | None = Field(default=None, alias="RAG_VECTOR_STORE_PATH")
    rag_chunk_size: int = Field(default=320, alias="RAG_CHUNK_SIZE")
    rag_chunk_overlap: int = Field(default=64, alias="RAG_CHUNK_OVERLAP")
    rag_top_k: int = Field(default=3, alias="RAG_TOP_K")
    analyze_failures: bool = Field(default=False, alias="ANALYZE_FAILURES")
    enable_remediation: bool = Field(default=False, alias="ENABLE_REMEDIATION")
    enable_release_orchestration: bool = Field(default=False, alias="ENABLE_RELEASE_ORCHESTRATION")


def get_settings() -> Settings:
    settings = Settings()
    settings.artifact_root = settings.artifact_root.resolve()
    settings.rag_source_root = settings.rag_source_root.resolve()
    if settings.rag_vector_store_path is not None:
        settings.rag_vector_store_path = settings.rag_vector_store_path.resolve()
    return settings