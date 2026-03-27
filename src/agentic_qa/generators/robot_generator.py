from __future__ import annotations

import re

from agentic_qa.domain.models import FeatureValidationRequest


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def _render_robot_context_comment(retrieved_context: str | None) -> str:
    if not retrieved_context:
        return ""
    return "\n".join(f"# {line}" if line else "#" for line in retrieved_context.splitlines()) + "\n"


def build_robot_suite_content(request: FeatureValidationRequest, retrieved_context: str | None = None) -> tuple[str, str]:
    feature_slug = _slugify(request.feature_name)
    filename = f"{feature_slug}.robot"
    negative_cases = request.negative_cases[:2]
    negative_tests = []
    for index, _negative_case in enumerate(negative_cases, start=1):
        negative_tests.append(
            f'''{feature_slug} negative {index}
    Create Session    api    ${{BASE_URL}}
    ${{response}}=    POST On Session    api    {request.target_endpoint.path}    json=${{REQUEST_PAYLOAD}}    headers=${{INVALID_HEADERS}}    expected_status=any
    Should Be True    ${{response.status_code}} >= 400'''
        )

    context_comment = _render_robot_context_comment(retrieved_context)

    content = f'''
{context_comment}*** Settings ***
Resource    ${{CURDIR}}/../resources/common.resource

*** Variables ***
${{ENDPOINT}}    {request.target_endpoint.path}
&{{REQUEST_PAYLOAD}}    {'    '.join(f'{key}={value}' for key, value in request.request_payload_example.items())}

*** Test Cases ***
{feature_slug} happy path
    Create Session    api    ${{BASE_URL}}
    ${{response}}=    {request.target_endpoint.method.upper()} On Session    api    ${{ENDPOINT}}    json=${{REQUEST_PAYLOAD}}    headers=${{VALID_HEADERS}}    expected_status={request.expected_status_code}
    Status Should Be    {request.expected_status_code}    ${{response}}
{chr(10).join(negative_tests)}
'''.strip() + "\n"
    return filename, content