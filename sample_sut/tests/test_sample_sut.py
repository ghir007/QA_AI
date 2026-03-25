from fastapi.testclient import TestClient

from sample_sut.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_widget_happy_path() -> None:
    response = client.post(
        "/api/v1/widgets",
        headers={"X-API-Key": "demo-key"},
        json={"name": "smoke-widget", "priority": "high"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "created"
    assert body["name"] == "smoke-widget"


def test_widgets_ui_page_is_available() -> None:
    response = client.get("/widgets/ui")

    assert response.status_code == 200
    assert "Create Widget" in response.text
    assert "create-widget-form" in response.text