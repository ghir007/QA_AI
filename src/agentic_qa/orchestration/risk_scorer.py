from __future__ import annotations

from abc import ABC, abstractmethod

from agentic_qa.domain.models import FeatureValidationRequest, RiskScore, RunSummary
from agentic_qa.domain.statuses import RunStatus


class RiskScorer(ABC):
    @abstractmethod
    def score(self, request: FeatureValidationRequest, prior_summary: RunSummary | None) -> RiskScore:
        raise NotImplementedError


class RuleBasedRiskScorer(RiskScorer):
    def score(self, request: FeatureValidationRequest, prior_summary: RunSummary | None) -> RiskScore:
        score = 0.0
        factors: list[str] = []

        if prior_summary is None:
            score = max(score, 0.5)
            factors.append("No prior run was found; use a medium baseline for new or unresolved work.")
        elif prior_summary.overall_status in {RunStatus.FAILED, RunStatus.GENERATION_FAILED}:
            score = max(score, 0.85)
            factors.append("Prior run failed, which elevates this request to high risk.")
        elif prior_summary.overall_status == RunStatus.PARTIAL_SUCCESS:
            score = max(score, 0.55)
            factors.append("Prior run partially succeeded, which keeps this request at medium risk.")
        else:
            score = max(score, 0.2)
            factors.append("Prior run passed, so the baseline risk stays low.")

        if request.negative_cases:
            score += 0.1
            factors.append("Negative-path coverage is requested, which increases risk surface.")

        if request.enable_browser_validation:
            score += 0.05
            factors.append("Browser validation is requested, which slightly increases execution complexity.")

        score = min(score, 1.0)
        if score >= 0.75:
            level = "high"
        elif score >= 0.4:
            level = "medium"
        else:
            level = "low"

        return RiskScore(
            request_id=request.request_id,
            feature_name=request.feature_name,
            risk_level=level,
            risk_score=round(score, 2),
            risk_factors=factors,
        )