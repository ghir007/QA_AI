from pathlib import Path

from agentic_qa.adapters.rag_placeholder import create_local_rag_adapter


def test_seed_docs_retrieve_relevant_widget_context() -> None:
    source_root = Path(__file__).resolve().parents[2] / "docs" / "rag-seeds"
    adapter = create_local_rag_adapter(source_root, chunk_size=220, chunk_overlap=40, top_k=1)

    class RequestStub:
        feature_name = "create widget"
        feature_description = "validate widget creation and auth behavior"

        class target_endpoint:
            method = "POST"
            path = "/api/v1/widgets"

        expected_status_code = 201
        expected_response_fields = ["id", "name", "priority", "status"]
        negative_cases = ["invalid_auth"]

    context = adapter.retrieve_context(RequestStub())

    assert "widget-requirements.md" in context or "widget-api-spec.json" in context
    assert "demo-key" in context or "/api/v1/widgets" in context