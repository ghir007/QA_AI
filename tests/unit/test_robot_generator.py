from agentic_qa.domain.models import FeatureValidationRequest, TargetEndpoint
from agentic_qa.generators.robot_generator import build_robot_suite_content


def test_robot_generator_contains_happy_path() -> None:
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

    filename, content = build_robot_suite_content(request)

    assert filename == "create_widget.robot"
    assert "create_widget happy path" in content
    assert "POST On Session" in content