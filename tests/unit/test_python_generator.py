from agentic_qa.domain.models import FeatureValidationRequest, TargetEndpoint
from agentic_qa.generators.python_generator import build_python_test_content


def test_python_generator_contains_happy_path() -> None:
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

    filename, content = build_python_test_content(request, "http://127.0.0.1:8010")

    assert filename == "test_api_create_widget.py"
    assert "test_create_widget_happy_path" in content
    assert "assert response.status_code == 201" in content