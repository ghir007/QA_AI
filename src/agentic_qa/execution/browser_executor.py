from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from agentic_qa.adapters.mcp_browser_adapter import MCPBrowserAdapter
from agentic_qa.domain.models import ExecutionMetrics


@dataclass
class BrowserExecutionResult:
    metrics: ExecutionMetrics
    artifacts: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


class BrowserExecutor(ABC):
    @abstractmethod
    def execute(self, script_path: Path, run_dir: Path, base_url: str) -> BrowserExecutionResult:
        raise NotImplementedError


class UnavailableBrowserExecutor(BrowserExecutor):
    def __init__(self, reason: str = "browser executor is not configured") -> None:
        self.reason = reason

    def execute(self, script_path: Path, run_dir: Path, base_url: str) -> BrowserExecutionResult:
        browser_dir = run_dir / "browser"
        log_path = browser_dir / "browser_execution.log"
        result_path = browser_dir / "browser_result.json"
        log_path.write_text(
            f"Browser validation skipped\nscript={script_path.name}\nbase_url={base_url}\nreason={self.reason}\n",
            encoding="utf-8",
        )
        result_path.write_text(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": self.reason,
                    "script": script_path.name,
                    "base_url": base_url,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return BrowserExecutionResult(
            metrics=ExecutionMetrics(status="skipped", passed=0, failed=0, exit_code=0),
            artifacts={"browser_log": log_path, "browser_result_json": result_path},
            errors=[self.reason],
        )


class FakeBrowserExecutor(BrowserExecutor):
    ONE_PIXEL_PNG = bytes.fromhex(
        "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
        "0000000D49444154789C6360000002000154A24F5D0000000049454E44AE426082"
    )

    def __init__(self, outcome: str = "passed") -> None:
        self.outcome = outcome

    def execute(self, script_path: Path, run_dir: Path, base_url: str) -> BrowserExecutionResult:
        browser_dir = run_dir / "browser"
        log_path = browser_dir / "browser_execution.log"
        result_path = browser_dir / "browser_result.json"
        screenshot_path = browser_dir / "browser_screenshot.png"
        script = json.loads(script_path.read_text(encoding="utf-8"))

        success = self.outcome == "passed"
        log_path.write_text(
            f"Fake browser executor\noutcome={self.outcome}\npage={script['page_path']}\nbase_url={base_url}\n",
            encoding="utf-8",
        )
        result_path.write_text(
            json.dumps(
                {
                    "status": "passed" if success else "failed",
                    "flow": script["flow"],
                    "page_path": script["page_path"],
                    "expected_result_text": script["expected"]["result_text"],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        screenshot_path.write_bytes(self.ONE_PIXEL_PNG)

        return BrowserExecutionResult(
            metrics=ExecutionMetrics(
                status="passed" if success else "failed",
                passed=1 if success else 0,
                failed=0 if success else 1,
                exit_code=0 if success else 1,
            ),
            artifacts={
                "browser_log": log_path,
                "browser_result_json": result_path,
                "browser_screenshot": screenshot_path,
            },
            errors=[] if success else ["fake browser validation failed"],
        )


class MCPBrowserExecutor(BrowserExecutor):
    def __init__(self, adapter: MCPBrowserAdapter) -> None:
        self.adapter = adapter

    def execute(self, script_path: Path, run_dir: Path, base_url: str) -> BrowserExecutionResult:
        response = self.adapter.execute_validation(script_path, base_url)
        browser_dir = run_dir / "browser"
        log_path = browser_dir / "browser_execution.log"
        result_path = browser_dir / "browser_result.json"
        log_path.write_text(
            f"MCP browser executor\navailable={response.available}\nsuccess={response.success}\nstdout={response.stdout}\nstderr={response.stderr}\n",
            encoding="utf-8",
        )
        result_path.write_text(
            json.dumps(
                {
                    "available": response.available,
                    "success": response.success,
                    "metadata": response.metadata,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        if not response.available:
            return BrowserExecutionResult(
                metrics=ExecutionMetrics(status="skipped", passed=0, failed=0, exit_code=0),
                artifacts={"browser_log": log_path, "browser_result_json": result_path},
                errors=[response.stderr or "mcp browser executor unavailable"],
            )

        return BrowserExecutionResult(
            metrics=ExecutionMetrics(
                status="passed" if response.success else "failed",
                passed=1 if response.success else 0,
                failed=0 if response.success else 1,
                exit_code=0 if response.success else 1,
            ),
            artifacts={"browser_log": log_path, "browser_result_json": result_path},
            errors=[] if response.success else [response.stderr or "mcp browser execution failed"],
        )


def create_browser_executor(executor_name: str, *, fake_outcome: str = "passed", mcp_endpoint: str | None = None, mcp_timeout_seconds: float = 5.0) -> BrowserExecutor:
    if executor_name == "fake":
        return FakeBrowserExecutor(outcome=fake_outcome)
    if executor_name == "mcp":
        return MCPBrowserExecutor(MCPBrowserAdapter(endpoint=mcp_endpoint, timeout_seconds=mcp_timeout_seconds))
    return UnavailableBrowserExecutor()