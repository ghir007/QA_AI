from pathlib import Path

from agentic_qa.domain.models import ExecutionMetrics, FailureReport, RunSummary
from agentic_qa.domain.statuses import RunStatus
from agentic_qa.remediation.rule_based import RuleBasedRemediationAdvisor


def _summary() -> RunSummary:
    return RunSummary(
        run_id="run-001",
        workflow_name="api_feature_validation_v1",
        overall_status=RunStatus.PARTIAL_SUCCESS,
        request_summary={"feature_name": "create widget", "endpoint": "/api/v1/widgets", "method": "POST"},
        plan={"step_count": 7, "generated_files": []},
        execution_summary={
            "python": ExecutionMetrics(status="failed", passed=0, failed=1, exit_code=1),
            "robot": ExecutionMetrics(status="passed", passed=1, failed=0, exit_code=0),
        },
        artifacts={},
        errors=[],
        started_at="2026-03-27T00:00:00Z",
        finished_at="2026-03-27T00:00:01Z",
    )


def _failure_report(classification: str) -> FailureReport:
    return FailureReport(
        classification=classification,
        confidence="high",
        explanation="diagnosis",
        suggested_next_action="next",
    )


def test_remediation_maps_test_config_error() -> None:
    plan = RuleBasedRemediationAdvisor().build_plan(_failure_report("test_config_error"), _summary(), Path("."))

    assert plan.requires_human_approval is True
    assert len(plan.actions) == 1
    assert plan.actions[0].action_type == "fix_generator"
    assert plan.actions[0].automated is False


def test_remediation_maps_environment_issue() -> None:
    plan = RuleBasedRemediationAdvisor().build_plan(_failure_report("environment_issue"), _summary(), Path("."))

    assert [action.action_type for action in plan.actions] == ["check_environment", "retry_run"]
    assert all(action.automated is False for action in plan.actions)


def test_remediation_maps_real_app_bug() -> None:
    plan = RuleBasedRemediationAdvisor().build_plan(_failure_report("real_app_bug"), _summary(), Path("."))

    assert len(plan.actions) == 1
    assert plan.actions[0].action_type == "manual_review"
    assert plan.requires_human_approval is True


def test_remediation_maps_assertion_drift() -> None:
    plan = RuleBasedRemediationAdvisor().build_plan(_failure_report("assertion_drift"), _summary(), Path("."))

    assert len(plan.actions) == 1
    assert plan.actions[0].action_type == "update_assertions"
    assert plan.actions[0].automated is False


def test_remediation_maps_flaky_suspect() -> None:
    plan = RuleBasedRemediationAdvisor().build_plan(_failure_report("flaky_suspect"), _summary(), Path("."))

    assert [action.action_type for action in plan.actions] == ["retry_run", "manual_review"]
    assert plan.requires_human_approval is True


def test_remediation_maps_clean() -> None:
    plan = RuleBasedRemediationAdvisor().build_plan(_failure_report("clean"), _summary(), Path("."))

    assert plan.actions == []
    assert plan.requires_human_approval is False