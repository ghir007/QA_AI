from __future__ import annotations

import json
import re

from agentic_qa.domain.models import FeatureValidationRequest


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")


def build_browser_validation_content(request: FeatureValidationRequest, sut_base_url: str) -> tuple[str, str]:
    feature_slug = _slugify(request.feature_name)
    filename = f"browser_validation_{feature_slug}.json"
    payload = {
        "flow": "widget_create_ui",
        "feature_name": request.feature_name,
        "base_url": sut_base_url,
        "page_path": "/widgets/ui",
        "submit_endpoint": request.target_endpoint.path,
        "method": request.target_endpoint.method.upper(),
        "form": {
            "name_selector": "#widget-name",
            "priority_selector": "#widget-priority",
            "submit_selector": "#submit-widget",
            "result_selector": "#result",
            "payload": request.request_payload_example,
        },
        "expected": {
            "status_code": request.expected_status_code,
            "result_text": "Widget created: widget-001",
        },
    }
    return filename, json.dumps(payload, indent=2) + "\n"