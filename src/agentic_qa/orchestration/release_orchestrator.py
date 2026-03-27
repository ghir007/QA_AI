from __future__ import annotations

import json
from pathlib import Path

from agentic_qa.domain.models import FeatureValidationRequest, ReleaseReadinessSummary, RiskScore, RunSummary, TargetEndpoint
from agentic_qa.domain.statuses import RunStatus
from agentic_qa.orchestration.risk_scorer import RiskScorer, RuleBasedRiskScorer
from agentic_qa.storage.artifact_store import ArtifactStore


class ReleaseOrchestrator:
    def __init__(self, scorer: RiskScorer | None = None) -> None:
        self.scorer = scorer or RuleBasedRiskScorer()

    def score_and_plan(
        self,
        requests: list[FeatureValidationRequest],
        prior_summaries: dict[str, RunSummary | None],
    ) -> ReleaseReadinessSummary:
        scored_requests = [self.scorer.score(request, prior_summaries.get(request.request_id)) for request in requests]
        blocking_risk_count = sum(
            1
            for request in requests
            if self.scorer.score(request, prior_summaries.get(request.request_id)).risk_level == "high"
            and prior_summaries.get(request.request_id) is not None
            and prior_summaries[request.request_id].overall_status in {RunStatus.FAILED, RunStatus.GENERATION_FAILED}
        )

        if any(score.risk_level == "high" for score in scored_requests):
            recommended_suite = "full_suite"
        elif all(score.risk_level == "low" for score in scored_requests):
            recommended_suite = "smoke_only"
        else:
            recommended_suite = "regression_subset"

        all_clean_or_low = all(
            score.risk_level == "low"
            or (
                prior_summaries.get(score.request_id) is not None
                and prior_summaries[score.request_id].overall_status == RunStatus.PASSED
            )
            for score in scored_requests
        )

        if blocking_risk_count > 0:
            release_recommendation = "hold"
        elif all_clean_or_low:
            release_recommendation = "go"
        else:
            release_recommendation = "conditional_go"

        advisory_note = self._build_advisory_note(scored_requests, blocking_risk_count, release_recommendation)

        return ReleaseReadinessSummary(
            scored_requests=scored_requests,
            recommended_suite=recommended_suite,
            release_recommendation=release_recommendation,
            advisory_note=advisory_note,
            blocking_risk_count=blocking_risk_count,
            total_requests=len(scored_requests),
        )

    @staticmethod
    def _build_advisory_note(
        scored_requests: list[RiskScore],
        blocking_risk_count: int,
        release_recommendation: str,
    ) -> str:
        if not scored_requests:
            return "No scoreable requests were found for release-readiness planning."
        if blocking_risk_count > 0:
            return "At least one high-risk request has a prior failing run, so release readiness should remain on hold."
        if release_recommendation == "go":
            return "All scored requests are clean or low risk, so the release can proceed with the recommended suite."
        return "Some requests still carry medium or unresolved risk, so release readiness should stay conditional pending review."


def load_requests_and_summaries_from_run_ids(
    artifact_store: ArtifactStore,
    run_ids: list[str],
) -> tuple[list[FeatureValidationRequest], dict[str, RunSummary | None]]:
    requests: list[FeatureValidationRequest] = []
    prior_summaries: dict[str, RunSummary | None] = {}

    for run_id in run_ids:
        run_dir = artifact_store.root / run_id
        request_path = run_dir / "request.json"
        summary_path = run_dir / "summary.json"

        if request_path.exists():
            request_payload = json.loads(request_path.read_text(encoding="utf-8"))
            request = FeatureValidationRequest.model_validate(request_payload)
            requests.append(request)
            prior_summaries[request.request_id] = RunSummary.model_validate(json.loads(summary_path.read_text(encoding="utf-8"))) if summary_path.exists() else None
            continue

        requests.append(
            FeatureValidationRequest(
                request_id=run_id,
                feature_name="unknown_request",
                feature_description="No persisted request artifact was found for this run id.",
                target_endpoint=TargetEndpoint(path="/unknown", method="GET"),
                expected_status_code=200,
                request_payload_example={},
                expected_response_fields=[],
                negative_cases=[],
                execution_mode="both",
                enable_browser_validation=False,
                tags=["missing-run-artifact"],
            )
        )
        prior_summaries[run_id] = None

    return requests, prior_summaries