from __future__ import annotations

import re

from agentic_qa.domain.models import FeatureValidationRequest


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def build_python_test_content(request: FeatureValidationRequest, sut_base_url: str) -> tuple[str, str]:
    feature_slug = _slugify(request.feature_name)
    filename = f"test_api_{feature_slug}.py"
    negative_cases = request.negative_cases[:2]
    negative_blocks = []
    for index, negative_case in enumerate(negative_cases, start=1):
        negative_blocks.append(
            f'''
def test_{feature_slug}_negative_{index}() -> None:
    response = client.request(
        "{request.target_endpoint.method.upper()}",
        "{request.target_endpoint.path}",
        headers={{"X-API-Key": "invalid-key"}},
        json={request.request_payload_example!r},
    )
    assert response.status_code >= 400
'''.strip()
        )

    content = f'''
import httpx


BASE_URL = "{sut_base_url}"
client = httpx.Client(base_url=BASE_URL, timeout=10.0)


def test_{feature_slug}_happy_path() -> None:
    response = client.request(
        "{request.target_endpoint.method.upper()}",
        "{request.target_endpoint.path}",
        headers={{"X-API-Key": "demo-key"}},
        json={request.request_payload_example!r},
    )
    assert response.status_code == {request.expected_status_code}
    body = response.json()
    for field in {request.expected_response_fields!r}:
        assert field in body


{chr(10).join(negative_blocks)}
'''.strip() + "\n"
    return filename, content