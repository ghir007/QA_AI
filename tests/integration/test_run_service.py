from pathlib import Path

from fastapi.testclient import TestClient

from agentic_qa.domain.models import FeatureValidationRequest, TargetEndpoint
from agentic_qa.domain.models import ExecutionMetrics
from agentic_qa.execution.browser_executor import FakeBrowserExecutor, UnavailableBrowserExecutor
from agentic_qa.orchestration.run_service import RunService
from agentic_qa.storage.artifact_store import ArtifactStore
from agentic_qa.storage.run_store import RunStore
from sample_sut.main import app as sut_app


def _passed_metrics() -> ExecutionMetrics:
    return ExecutionMetrics(status="passed", passed=1, failed=0, exit_code=0)


def test_run_service_returns_generation_failed_when_generator_breaks(tmp_path, monkeypatch) -> None:
    request = FeatureValidationRequest(
        request_id="req-001",
        feature_name="create widget",
        feature_description="validate widget creation",
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example={"name": "smoke-widget", "priority": "high"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=["invalid_auth"],
        execution_mode="both",
        tags=["smoke"],
    )

    def broken_generator(*_args, **_kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr("agentic_qa.orchestration.run_service.build_python_test_content", broken_generator)
    class StubSettings:
        sample_sut_base_url = "http://127.0.0.1:8010"

    service = RunService(ArtifactStore(tmp_path / "runs"), RunStore(), StubSettings())

    summary = service.execute(request)

    assert summary.overall_status == "generation_failed"
    assert summary.errors
    assert summary.execution_summary["python"].status == "skipped"
    assert summary.execution_summary["robot"].status == "skipped"


def test_run_service_marks_browser_validation_unavailable(tmp_path, monkeypatch) -> None:
    request = FeatureValidationRequest(
        request_id="req-002",
        feature_name="create widget",
        feature_description="validate widget creation in browser",
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example={"name": "browser-widget", "priority": "normal"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=[],
        execution_mode="both",
        enable_browser_validation=True,
        tags=["browser"],
    )

    class StubSettings:
        sample_sut_base_url = "http://127.0.0.1:8010"

    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_python_test", lambda *_args, **_kwargs: _passed_metrics())
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_robot_suite", lambda *_args, **_kwargs: _passed_metrics())

    service = RunService(
        ArtifactStore(tmp_path / "runs"),
        RunStore(),
        StubSettings(),
        browser_executor=UnavailableBrowserExecutor("browser executor is not configured"),
    )

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == "skipped"
    assert summary.overall_status == "partial_success"
    assert any("browser executor is not configured" in error for error in summary.errors)
    assert "generated_browser_validation" in summary.artifacts
    assert "browser_log" in summary.artifacts


def test_run_service_keeps_browser_out_of_summary_when_disabled(tmp_path, monkeypatch) -> None:
    request = FeatureValidationRequest(
        request_id="req-003",
        feature_name="create widget",
        feature_description="validate widget creation",
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example={"name": "smoke-widget", "priority": "high"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=[],
        execution_mode="both",
        tags=["smoke"],
    )

    class StubSettings:
        sample_sut_base_url = "http://127.0.0.1:8010"

    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_python_test", lambda *_args, **_kwargs: _passed_metrics())
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_robot_suite", lambda *_args, **_kwargs: _passed_metrics())

    service = RunService(ArtifactStore(tmp_path / "runs"), RunStore(), StubSettings(), browser_executor=FakeBrowserExecutor())

    summary = service.execute(request)

    assert "browser" not in summary.execution_summary
    assert "generated_browser_validation" not in summary.artifacts


def test_run_service_browser_fake_success(tmp_path, monkeypatch) -> None:
    request = FeatureValidationRequest(
        request_id="req-004",
        feature_name="create widget",
        feature_description="validate widget creation in browser",
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example={"name": "browser-widget", "priority": "normal"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=[],
        execution_mode="both",
        enable_browser_validation=True,
        tags=["browser"],
    )

    class StubSettings:
        sample_sut_base_url = "http://127.0.0.1:8010"

    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_python_test", lambda *_args, **_kwargs: _passed_metrics())
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_robot_suite", lambda *_args, **_kwargs: _passed_metrics())

    service = RunService(
        ArtifactStore(tmp_path / "runs"),
        RunStore(),
        StubSettings(),
        browser_executor=FakeBrowserExecutor("passed"),
    )

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == "passed"
    assert summary.overall_status == "passed"
    assert "browser_screenshot" in summary.artifacts


def test_run_service_browser_fake_failure(tmp_path, monkeypatch) -> None:
    request = FeatureValidationRequest(
        request_id="req-005",
        feature_name="create widget",
        feature_description="validate widget creation in browser",
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example={"name": "browser-widget", "priority": "normal"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=[],
        execution_mode="both",
        enable_browser_validation=True,
        tags=["browser"],
    )

    class StubSettings:
        sample_sut_base_url = "http://127.0.0.1:8010"

    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_python_test", lambda *_args, **_kwargs: _passed_metrics())
    monkeypatch.setattr("agentic_qa.orchestration.run_service.execute_robot_suite", lambda *_args, **_kwargs: _passed_metrics())

    service = RunService(
        ArtifactStore(tmp_path / "runs"),
        RunStore(),
        StubSettings(),
        browser_executor=FakeBrowserExecutor("failed"),
    )

    summary = service.execute(request)

    assert summary.execution_summary["browser"].status == "failed"
    assert summary.overall_status == "partial_success"
    assert any("fake browser validation failed" in error for error in summary.errors)


def test_sample_sut_is_available_in_process() -> None:
    client = TestClient(sut_app)

    response = client.get("/health")

    assert response.status_code == 200