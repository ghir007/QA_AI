from pathlib import Path

from agentic_qa.domain.models import FeatureValidationRequest, TargetEndpoint
from agentic_qa.orchestration.planner import build_run_plan


def test_build_run_plan_creates_expected_steps() -> None:
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

    plan = build_run_plan(request, Path("artifacts/runs"))

    assert plan.workflow_name == "api_feature_validation_v1"
    assert len(plan.steps) == 7
    assert plan.steps[0].name == "plan_request"


def test_build_run_plan_adds_browser_steps_when_enabled() -> None:
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
        tags=["smoke"],
    )

    plan = build_run_plan(request, Path("artifacts/runs"))

    assert len(plan.steps) == 9
    assert [step.name for step in plan.steps] == [
        "plan_request",
        "generate_python_tests",
        "generate_robot_tests",
        "generate_browser_validation",
        "execute_python_tests",
        "execute_robot_tests",
        "execute_browser_validation",
        "collect_artifacts",
        "build_summary",
    ]