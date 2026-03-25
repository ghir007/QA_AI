import json

from agentic_qa.domain.models import FeatureValidationRequest, TargetEndpoint
from agentic_qa.generators.browser_generator import build_browser_validation_content


def test_browser_generator_creates_deterministic_artifact() -> None:
    request = FeatureValidationRequest(
        request_id="req-browser-001",
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

    filename, content = build_browser_validation_content(request, "http://127.0.0.1:8010")
    payload = json.loads(content)

    assert filename == "browser_validation_create_widget.json"
    assert payload["page_path"] == "/widgets/ui"
    assert payload["form"]["payload"]["name"] == "browser-widget"
    assert payload["expected"]["result_text"] == "Widget created: widget-001"