from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MCPBrowserExecutionResponse:
    available: bool
    success: bool
    stdout: str = ""
    stderr: str = ""
    artifacts: dict[str, bytes | str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPBrowserAdapter:
    """Narrow boundary for future MCP-backed browser execution."""

    def __init__(self, endpoint: str | None, timeout_seconds: float = 5.0) -> None:
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        return bool(self.endpoint)

    def execute_validation(self, script_path: Path, base_url: str) -> MCPBrowserExecutionResponse:
        if not self.is_available():
            return MCPBrowserExecutionResponse(
                available=False,
                success=False,
                stderr="MCP browser endpoint is not configured.",
                metadata={"script_path": str(script_path), "base_url": base_url},
            )

        return MCPBrowserExecutionResponse(
            available=False,
            success=False,
            stderr="Live MCP browser execution is not implemented in this slice.",
            metadata={"script_path": str(script_path), "base_url": base_url, "endpoint": self.endpoint},
        )