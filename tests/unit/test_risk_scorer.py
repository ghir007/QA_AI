from agentic_qa.domain.models import ExecutionMetrics, FeatureValidationRequest, RunSummary, TargetEndpoint
from agentic_qa.domain.statuses import RunStatus
from agentic_qa.orchestration.risk_scorer import RuleBasedRiskScorer


def _request(*, request_id: str = "req-001", negative_cases: list[str] | None = None, enable_browser_validation: bool = False) -> FeatureValidationRequest:
    return FeatureValidationRequest(
        request_id=request_id,
        feature_name="create widget",
        feature_description="validate widget creation",
        target_endpoint=TargetEndpoint(path="/api/v1/widgets", method="POST"),
        expected_status_code=201,
        request_payload_example={"name": "smoke-widget", "priority": "high"},
        expected_response_fields=["id", "name", "priority", "status"],
        negative_cases=negative_cases or [],
        execution_mode="both",
        enable_browser_validation=enable_browser_validation,
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


def test_risk_scorer_marks_prior_failure_as_high() -> None:
    score = RuleBasedRiskScorer().score(_request(), _summary(RunStatus.FAILED))

    assert score.risk_level == "high"
    assert score.risk_score >= 0.75


def test_risk_scorer_marks_partial_success_as_medium() -> None:
    score = RuleBasedRiskScorer().score(_request(), _summary(RunStatus.PARTIAL_SUCCESS))

    assert score.risk_level == "medium"


def test_risk_scorer_elevates_negative_cases() -> None:
    score = RuleBasedRiskScorer().score(_request(negative_cases=["invalid_auth"]), _summary(RunStatus.PASSED))

    assert score.risk_score > 0.2
    assert any("Negative-path coverage" in factor for factor in score.risk_factors)


def test_risk_scorer_elevates_browser_request() -> None:
    score = RuleBasedRiskScorer().score(_request(enable_browser_validation=True), _summary(RunStatus.PASSED))

    assert score.risk_score > 0.2
    assert any("Browser validation" in factor for factor in score.risk_factors)


def test_risk_scorer_uses_medium_baseline_for_new_request() -> None:
    score = RuleBasedRiskScorer().score(_request(), None)

    assert score.risk_level == "medium"
    assert score.risk_score >= 0.5