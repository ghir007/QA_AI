from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

from pydantic import BaseModel, Field

from agentic_qa.domain.statuses import RunStatus, StepStatus


class TargetEndpoint(BaseModel):
    path: str
    method: str


class FeatureValidationRequest(BaseModel):
    request_id: str
    feature_name: str
    feature_description: str
    target_endpoint: TargetEndpoint
    expected_status_code: int
    request_payload_example: dict[str, Any]
    expected_response_fields: list[str]
    negative_cases: list[str] = Field(default_factory=list)
    execution_mode: str = "both"
    enable_browser_validation: bool = False
    tags: list[str] = Field(default_factory=list)


class RunStep(BaseModel):
    name: str
    status: StepStatus = StepStatus.PENDING
    detail: str | None = None


class RunPlan(BaseModel):
    run_id: str
    workflow_name: str = "api_feature_validation_v1"
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_snapshot: FeatureValidationRequest
    steps: list[RunStep]
    artifact_root: str
    status: RunStatus = RunStatus.PLANNED


class ExecutionMetrics(BaseModel):
    status: str
    passed: int = 0
    failed: int = 0
    exit_code: int = 0


class RunSummary(BaseModel):
    run_id: str
    workflow_name: str
    overall_status: RunStatus
    request_summary: dict[str, str]
    plan: dict[str, Any]
    execution_summary: dict[str, ExecutionMetrics]
    artifacts: dict[str, str]
    errors: list[str] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime


def empty_execution_summary(include_browser: bool = False) -> dict[str, ExecutionMetrics]:
    skipped = ExecutionMetrics(status="skipped", passed=0, failed=0, exit_code=0)
    summary = {
        "python": skipped.model_copy(),
        "robot": skipped.model_copy(),
    }
    if include_browser:
        summary["browser"] = skipped.model_copy()
    return summary