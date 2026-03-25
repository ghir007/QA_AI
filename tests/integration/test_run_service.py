from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

from agentic_qa.adapters.mcp_browser_adapter import MCPBrowserAdapter
from agentic_qa.domain.models import ExecutionMetrics
from agentic_qa.domain.models import FeatureValidationRequest, TargetEndpoint
from agentic_qa.execution.browser_executor import MCPBrowserExecutor, FakeBrowserExecutor, UnavailableBrowserExecutor
from agentic_qa.orchestration.run_service import RunService
from agentic_qa.storage.artifact_store import ArtifactStore
from agentic_qa.storage.run_store import RunStore
from sample_sut.main import app as sut_app


def _passed_metrics() -> ExecutionMetrics:
    return ExecutionMetrics(status="passed", passed=1, failed=0, exit_code=0)


def _failed_metrics() -> ExecutionMetrics:
    return ExecutionMetrics(status="failed", passed=0, failed=1, exit_code=1)


class StubSettings:
    sample_sut_base_url = "http://127.0.0.1:8010"


def _build_request(
    *,
    request_id: str,
    feature_description: str = "validate widget creation",
    payload: dict | None = None,
    negative_cases: list[str] | None = None,
    enable_browser_validation: bool = False,
    tags: list[str] | None = None,
) -> FeatureValidationRequest:
    return FeatureValidationRequest(
        request_id=request_id,
        feature_name="create widget",
        feature_description=feature_description,
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example=payload or {"name": "smoke-widget", "priority": "high"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=negative_cases or [],
        execution_mode="both",
        enable_browser_validation=enable_browser_validation,
        tags=tags or ["smoke"],
    )


@pytest.fixture
def service_factory(tmp_path):
    def _create(browser_executor=None) -> tuple[RunService, pytest.TempPathFactory | object]:
        artifact_store = ArtifactStore(tmp_path / "runs")
        service = RunService(artifact_store, RunStore(), StubSettings(), browser_executor=browser_executor)
        return service, artifact_store.root

    return _create


def _stub_api_and_robot_success(monkeypatch) -> None:
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_python_test", lambda *_args, **_kwargs: _passed_metrics())
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_robot_suite", lambda *_args, **_kwargs: _passed_metrics())


def _stub_api_and_robot_failure(monkeypatch) -> None:
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_python_test", lambda *_args, **_kwargs: _failed_metrics())
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_robot_suite", lambda *_args, **_kwargs: _failed_metrics())


def _assert_artifacts_exist(summary, artifact_root, *artifact_keys: str) -> None:
    for artifact_key in artifact_keys:
        assert artifact_key in summary.artifacts
        assert (artifact_root / summary.artifacts[artifact_key]).exists()


def test_run_service_returns_generation_failed_when_generator_breaks(service_factory, monkeypatch) -> None:
    request = _build_request(request_id="req-001", negative_cases=["invalid_auth"])

    def broken_generator(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("agentic_qa.orchestration.run_service.build_python_test_content", broken_generator)
    service, artifact_root = service_factory()

    summary = service.execute(request)

    assert summary.overall_status == "generation_failed"
    assert summary.errors
    assert summary.execution_summary["python"].status == "skipped"
    assert summary.execution_summary["robot"].status == "skipped"
    _assert_artifacts_exist(summary, artifact_root, "plan_json")


def test_run_service_marks_browser_validation_unavailable(service_factory, monkeypatch) -> None:
    request = _build_request(
        request_id="req-002",
        feature_description="validate widget creation in browser",
        payload={"name": "browser-widget", "priority": "normal"},
        enable_browser_validation=True,
        tags=["browser"],
    )

    _stub_api_and_robot_success(monkeypatch)
    service, artifact_root = service_factory(
        browser_executor=UnavailableBrowserExecutor("browser executor is not configured")
    )

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == "skipped"
    assert summary.overall_status == "passed"
    assert any("browser executor is not configured" in error for error in summary.errors)
    _assert_artifacts_exist(
        summary,
        artifact_root,
        "plan_json",
        "generated_python_test",
        "generated_robot_suite",
        "generated_browser_validation",
        "browser_log",
        "browser_result_json",
    )


def test_run_service_keeps_browser_out_of_summary_when_disabled(service_factory, monkeypatch) -> None:
    request = _build_request(request_id="req-003")

    _stub_api_and_robot_success(monkeypatch)
    service, artifact_root = service_factory(browser_executor=FakeBrowserExecutor())

    summary = service.execute(request)

    assert "browser" not in summary.execution_summary
    assert "generated_browser_validation" not in summary.artifacts
    _assert_artifacts_exist(
        summary,
        artifact_root,
        "plan_json",
        "generated_python_test",
        "generated_robot_suite",
    )


@pytest.mark.parametrize(
    ("browser_outcome", "expected_browser_status", "expected_overall_status", "expected_error"),
    [
        ("passed", "passed", "passed", None),
        ("failed", "failed", "partial_success", "fake browser validation failed"),
    ],
)
def test_run_service_browser_fake_outcomes(
    service_factory,
    monkeypatch,
    browser_outcome: str,
    expected_browser_status: str,
    expected_overall_status: str,
    expected_error: str | None,
) -> None:
    request = _build_request(
        request_id=f"req-browser-{browser_outcome}",
        feature_description="validate widget creation in browser",
        payload={"name": "browser-widget", "priority": "normal"},
        enable_browser_validation=True,
        tags=["browser"],
    )

    _stub_api_and_robot_success(monkeypatch)
    service, artifact_root = service_factory(browser_executor=FakeBrowserExecutor(browser_outcome))

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == expected_browser_status
    assert summary.overall_status == expected_overall_status
    if expected_error is None:
        assert not summary.errors
    else:
        assert any(expected_error in error for error in summary.errors)
    _assert_artifacts_exist(
        summary,
        artifact_root,
        "plan_json",
        "generated_python_test",
        "generated_robot_suite",
        "generated_browser_validation",
        "browser_log",
        "browser_result_json",
        "browser_screenshot",
    )


def test_run_service_mcp_browser_happy_path(service_factory, monkeypatch) -> None:
    request = _build_request(
        request_id="req-browser-mcp",
        feature_description="validate widget creation in browser through MCP",
        payload={"name": "browser-widget", "priority": "normal"},
        enable_browser_validation=True,
        tags=["browser", "mcp"],
    )
    monkeypatch.setenv("MCP_DEMO_MODE", "passed")
    _stub_api_and_robot_success(monkeypatch)
    demo_server = Path(__file__).resolve().parents[1] / "unit" / "mcp_demo_server.py"
    executor = MCPBrowserExecutor(
        MCPBrowserAdapter(
            command=sys.executable,
            args=[str(demo_server)],
            tool_name="browser_validate_ui",
        )
    )
    service, artifact_root = service_factory(browser_executor=executor)

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == "passed"
    assert summary.overall_status == "passed"
    _assert_artifacts_exist(
        summary,
        artifact_root,
        "generated_browser_validation",
        "browser_log",
        "browser_result_json",
        "browser_screenshot",
    )


def test_run_service_mcp_browser_failure_is_partial_success(service_factory, monkeypatch) -> None:
    request = _build_request(
        request_id="req-browser-mcp-failed",
        feature_description="validate widget creation in browser through MCP",
        payload={"name": "browser-widget", "priority": "normal"},
        enable_browser_validation=True,
        tags=["browser", "mcp"],
    )
    monkeypatch.setenv("MCP_DEMO_MODE", "failed")
    _stub_api_and_robot_success(monkeypatch)
    demo_server = Path(__file__).resolve().parents[1] / "unit" / "mcp_demo_server.py"
    executor = MCPBrowserExecutor(
        MCPBrowserAdapter(
            command=sys.executable,
            args=[str(demo_server)],
            tool_name="browser_validate_ui",
        )
    )
    service, artifact_root = service_factory(browser_executor=executor)

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == "failed"
    assert summary.overall_status == "partial_success"
    _assert_artifacts_exist(
        summary,
        artifact_root,
        "generated_browser_validation",
        "browser_log",
        "browser_result_json",
        "browser_screenshot",
    )


def test_run_service_mcp_browser_invalid_result_json_is_skipped(service_factory, monkeypatch) -> None:
    request = _build_request(
        request_id="req-browser-mcp-invalid-result",
        feature_description="validate widget creation in browser through MCP",
        payload={"name": "browser-widget", "priority": "normal"},
        enable_browser_validation=True,
        tags=["browser", "mcp"],
    )
    monkeypatch.setenv("MCP_DEMO_MODE", "invalid_result_json")
    _stub_api_and_robot_success(monkeypatch)
    demo_server = Path(__file__).resolve().parents[1] / "unit" / "mcp_demo_server.py"
    executor = MCPBrowserExecutor(
        MCPBrowserAdapter(
            command=sys.executable,
            args=[str(demo_server)],
            tool_name="browser_validate_ui",
        )
    )
    service, artifact_root = service_factory(browser_executor=executor)

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == "skipped"
    assert summary.overall_status == "passed"
    _assert_artifacts_exist(
        summary,
        artifact_root,
        "generated_browser_validation",
        "browser_log",
        "browser_result_json",
    )


def test_run_service_status_policy_with_real_failures_and_browser_skipped(service_factory, monkeypatch) -> None:
    request = _build_request(
        request_id="req-006",
        feature_description="validate widget creation in browser",
        payload={"name": "browser-widget", "priority": "normal"},
        enable_browser_validation=True,
        tags=["browser"],
    )

    _stub_api_and_robot_failure(monkeypatch)
    service, artifact_root = service_factory(
        browser_executor=UnavailableBrowserExecutor("browser executor is not configured")
    )

    summary = service.execute(request)

    assert summary.execution_summary["python"].status == "failed"
    assert summary.execution_summary["robot"].status == "failed"
    assert summary.execution_summary["browser"].status == "skipped"
    assert summary.overall_status == "failed"
    _assert_artifacts_exist(
        summary,
        artifact_root,
        "generated_browser_validation",
        "browser_log",
        "browser_result_json",
    )


def test_sample_sut_is_available_in_process() -> None:
    client = TestClient(sut_app)

    response = client.get("/health")

    assert response.status_code == 200