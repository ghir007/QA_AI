from agentic_qa.domain.models import ExecutionMetrics, FeatureValidationRequest, RunSummary, TargetEndpoint
from agentic_qa.domain.statuses import RunStatus
from agentic_qa.orchestration.release_orchestrator import ReleaseOrchestrator


def _request(request_id: str, *, negative_cases: list[str] | None = None, browser: bool = False) -> FeatureValidationRequest:
    return FeatureValidationRequest(
        request_id=request_id,
        feature_name=f"feature-{request_id}",
        feature_description="validate feature",
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example={"name": "smoke-widget", "priority": "high"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=negative_cases or [],
        execution_mode="both",
        enable_browser_validation=browser,
        tags=["smoke"],
    )


def _summary(status: RunStatus) -> RunSummary:
    return RunSummary(
        run_id="run-001",
        workflow_name="api_feature_validation_v1",
        overall_status=status,
        request_summary={"feature_name": "create widget", "endpoint": "/api/v1/widgets", "method": "POST"},
        plan={"step_count": 7, "generated_files": []},
        execution_summary={
            "python": ExecutionMetrics(status="passed", passed=1, failed=0, exit_code=0),
            "robot": ExecutionMetrics(status="passed", passed=1, failed=0, exit_code=0),
        },
        artifacts={},
        errors=[],
        started_at="2026-03-27T00:00:00Z",
        finished_at="2026-03-27T00:00:01Z",
    )


def test_release_orchestrator_recommends_full_suite_for_high_risk() -> None:
    orchestrator = ReleaseOrchestrator()
    request = _request("req-001")

    summary = orchestrator.score_and_plan([request], {"req-001": _summary(RunStatus.FAILED)})

    assert summary.recommended_suite == "full_suite"
    assert summary.release_recommendation == "hold"


def test_release_orchestrator_recommends_smoke_only_for_low_risk() -> None:
    orchestrator = ReleaseOrchestrator()
    request = _request("req-001")

    summary = orchestrator.score_and_plan([request], {"req-001": _summary(RunStatus.PASSED)})

    assert summary.recommended_suite == "smoke_only"
    assert summary.release_recommendation == "go"


def test_release_orchestrator_recommends_regression_subset_for_mixed_risk() -> None:
    orchestrator = ReleaseOrchestrator()
    requests = [_request("req-001"), _request("req-002", negative_cases=["invalid_auth"], browser=True)]

    summary = orchestrator.score_and_plan(
        requests,
        {"req-001": _summary(RunStatus.PASSED), "req-002": _summary(RunStatus.PARTIAL_SUCCESS)},
    )

    assert summary.recommended_suite == "regression_subset"
    assert summary.release_recommendation == "conditional_go"