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


class FailureReport(BaseModel):
    classification: str
    confidence: str
    explanation: str
    suggested_next_action: str


class RemediationAction(BaseModel):
    action_type: str
    description: str
    automated: bool
    priority: str


class RemediationPlan(BaseModel):
    actions: list[RemediationAction] = Field(default_factory=list)
    requires_human_approval: bool
    advisory_note: str


class RiskScore(BaseModel):
    request_id: str
    feature_name: str
    risk_level: str
    risk_score: float
    risk_factors: list[str] = Field(default_factory=list)


class ReleaseReadinessSummary(BaseModel):
    scored_requests: list[RiskScore] = Field(default_factory=list)
    recommended_suite: str
    release_recommendation: str
    advisory_note: str
    blocking_risk_count: int
    total_requests: int


class RunSummary(BaseModel):
    run_id: str
    workflow_name: str
    overall_status: RunStatus
    request_summary: dict[str, str]
    plan: dict[str, Any]
    execution_summary: dict[str, ExecutionMetrics]
    artifacts: dict[str, str]
    errors: list[str] = Field(default_factory=list)
    failure_analysis: FailureReport | None = None
    remediation_plan: RemediationPlan | None = None
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