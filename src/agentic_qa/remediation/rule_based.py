from __future__ import annotations

from pathlib import Path

from agentic_qa.domain.models import FailureReport, RemediationAction, RemediationPlan, RunSummary
from agentic_qa.remediation.base import RemediationAdvisor


class RuleBasedRemediationAdvisor(RemediationAdvisor):
    def build_plan(self, failure_report: FailureReport, summary: RunSummary, run_dir: Path) -> RemediationPlan:
        classification = failure_report.classification

        if classification == "test_config_error":
            return RemediationPlan(
                actions=[
                    RemediationAction(
                        action_type="fix_generator",
                        description="Inspect generation inputs and generator output paths, then correct the broken generator or test configuration before rerunning.",
                        automated=False,
                        priority="high",
                    )
                ],
                requires_human_approval=True,
                advisory_note="Generation failed before execution, so the next step should stay focused on fixing deterministic generation or configuration issues.",
            )

        if classification == "environment_issue":
            return RemediationPlan(
                actions=[
                    RemediationAction(
                        action_type="check_environment",
                        description="Verify the sample SUT process, network reachability, and timeout-related environment assumptions before rerunning.",
                        automated=False,
                        priority="high",
                    ),
                    RemediationAction(
                        action_type="retry_run",
                        description="Rerun the same workflow after the environment checks pass to confirm the issue was transient rather than behavioral.",
                        automated=False,
                        priority="medium",
                    ),
                ],
                requires_human_approval=True,
                advisory_note="Environment findings should be validated manually before any retry is trusted.",
            )

        if classification == "real_app_bug":
            return RemediationPlan(
                actions=[
                    RemediationAction(
                        action_type="manual_review",
                        description="Review the persisted logs and generated tests across the disagreeing execution paths to confirm a real application defect.",
                        automated=False,
                        priority="high",
                    )
                ],
                requires_human_approval=True,
                advisory_note="Cross-path disagreement suggests a real defect and should be reviewed by an engineer before any follow-up change is attempted.",
            )

        if classification == "assertion_drift":
            return RemediationPlan(
                actions=[
                    RemediationAction(
                        action_type="update_assertions",
                        description="Align generated assertions with the expected_response_fields contract captured in the persisted request artifact.",
                        automated=False,
                        priority="medium",
                    )
                ],
                requires_human_approval=True,
                advisory_note="Assertion drift should be corrected deliberately to avoid weakening the contract checks.",
            )

        if classification == "flaky_suspect":
            return RemediationPlan(
                actions=[
                    RemediationAction(
                        action_type="retry_run",
                        description="Rerun the workflow unchanged to determine whether the partial-success signal is repeatable.",
                        automated=False,
                        priority="medium",
                    ),
                    RemediationAction(
                        action_type="manual_review",
                        description="Review persisted logs and artifacts if the rerun reproduces the same ambiguous signal.",
                        automated=False,
                        priority="medium",
                    ),
                ],
                requires_human_approval=True,
                advisory_note="Ambiguous partial-success outcomes should be rechecked before stronger conclusions are drawn.",
            )

        if classification == "clean":
            return RemediationPlan(
                actions=[],
                requires_human_approval=False,
                advisory_note="No remediation is recommended because the run completed cleanly.",
            )

        return RemediationPlan(
            actions=[
                RemediationAction(
                    action_type="manual_review",
                    description="Review the persisted evidence manually because no specific deterministic remediation mapping was available.",
                    automated=False,
                    priority="low",
                )
            ],
            requires_human_approval=True,
            advisory_note="Fallback advisory path used because the classification was not explicitly mapped.",
        )