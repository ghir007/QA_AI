import json

from agentic_qa.execution.browser_executor import FakeBrowserExecutor, UnavailableBrowserExecutor


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
    script_path = tmp_path / "generated" / "browser_validation_create_widget.json"
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        json.dumps({"flow": "widget_create_ui", "page_path": "/widgets/ui", "expected": {"result_text": "Widget created: widget-001"}}),
        encoding="utf-8",
    )
    run_dir = tmp_path
    (run_dir / "browser").mkdir(exist_ok=True)

    result = FakeBrowserExecutor("passed").execute(script_path, run_dir, "http://127.0.0.1:8010")

    assert result.metrics.status == "passed"
    assert result.artifacts["browser_screenshot"].exists()