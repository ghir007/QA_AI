import json
import sys
from pathlib import Path

from agentic_qa.adapters.mcp_browser_adapter import MCPBrowserAdapter
from agentic_qa.execution.browser_executor import MCPBrowserExecutor, FakeBrowserExecutor, UnavailableBrowserExecutor


def _browser_validation_script(tmp_path: Path) -> Path:
    script_path = tmp_path / "generated" / "browser_validation_create_widget.json"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        json.dumps(
            {
                "flow": "widget_create_ui",
                "page_path": "/widgets/ui",
                "expected": {"result_text": "Widget created: widget-001"},
            }
        ),
        encoding="utf-8",
    )
    return script_path


def _mcp_executor(timeout_seconds: float = 5.0) -> MCPBrowserExecutor:
    return MCPBrowserExecutor(
        MCPBrowserAdapter(
            command=sys.executable,
            args=[str(Path(__file__).with_name("mcp_demo_server.py"))],
            tool_name="browser_validate_ui",
            timeout_seconds=timeout_seconds,
        )
    )


def _mcp_adapter(timeout_seconds: float = 5.0) -> MCPBrowserAdapter:
    return MCPBrowserAdapter(
        command=sys.executable,
        args=[str(Path(__file__).with_name("mcp_demo_server.py"))],
        tool_name="browser_validate_ui",
        timeout_seconds=timeout_seconds,
    )


def test_unavailable_browser_executor_writes_skip_artifacts(tmp_path) -> None:
    script_path = tmp_path / "generated" / "browser_validation_create_widget.json"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("{}", encoding="utf-8")
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)

    result = UnavailableBrowserExecutor("not configured").execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "skipped"
    assert "not configured" in result.errors[0]
    assert result.artifacts["browser_log"].exists()
    assert result.artifacts["browser_result_json"].exists()


def test_fake_browser_executor_writes_success_artifacts(tmp_path) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)

    result = FakeBrowserExecutor("passed").execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "passed"
    assert result.artifacts["browser_screenshot"].exists()


def test_mcp_browser_executor_writes_real_mcp_demo_artifacts(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "passed")

    result = _mcp_executor().execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "passed"
    assert result.artifacts["browser_log"].exists()
    assert result.artifacts["browser_result_json"].exists()
    assert result.artifacts["browser_screenshot"].exists()


def test_mcp_browser_executor_ignores_notifications_before_response(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "notify_first")

    result = _mcp_executor().execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "passed"
    assert not result.errors


def test_mcp_browser_executor_skips_when_server_times_out(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "hang")

    result = _mcp_executor(timeout_seconds=0.1).execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "skipped"
    assert any("timed out" in error for error in result.errors)
    assert result.artifacts["browser_log"].exists()
    assert result.artifacts["browser_result_json"].exists()


def test_mcp_browser_executor_skips_on_protocol_error(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "protocol_error")

    result = _mcp_executor().execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "skipped"
    assert any("browser tool failed" in error for error in result.errors)


def test_mcp_browser_executor_skips_on_invalid_artifact_payload(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "invalid_artifact")

    result = _mcp_executor().execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "skipped"
    assert any("Incorrect padding" in error or "Invalid base64" in error or "number of data characters" in error for error in result.errors)


def test_mcp_browser_executor_skips_on_invalid_result_json(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "invalid_result_json")

    result = _mcp_executor().execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "skipped"
    assert any("malformed json" in error for error in result.errors)
    assert result.artifacts["browser_log"].exists()
    assert result.artifacts["browser_result_json"].exists()


def test_mcp_browser_adapter_reports_missing_validation_file(tmp_path) -> None:
    response = _mcp_adapter().execute_validation(tmp_path / "missing.json", "http://127.0.0.1:8010")

    assert response.available is False
    assert response.success is False
    assert "Failed to read MCP browser validation artifact" in response.stderr


def test_mcp_browser_adapter_reports_malformed_validation_json(tmp_path) -> None:
    script_path = tmp_path / "generated" / "browser_validation_create_widget.json"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text("{not-json", encoding="utf-8")

    response = _mcp_adapter().execute_validation(script_path, "http://127.0.0.1:8010")

    assert response.available is False
    assert response.success is False
    assert "MCP browser validation artifact was malformed JSON" in response.stderr


def test_mcp_browser_executor_skips_on_invalid_content_length(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "invalid_content_length")

    result = _mcp_executor().execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "skipped"
    assert any("content-length was invalid" in error for error in result.errors)


def test_mcp_browser_executor_skips_on_non_dict_structured_content(tmp_path, monkeypatch) -> None:
    script_path = _browser_validation_script(tmp_path)
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)
    monkeypatch.setenv("MCP_DEMO_MODE", "non_dict_structured_content")

    result = _mcp_executor().execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "skipped"
    assert any("structuredContent was not an object" in error for error in result.errors)