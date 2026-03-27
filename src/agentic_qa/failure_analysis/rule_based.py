from __future__ import annotations

import json
from pathlib import Path

from agentic_qa.domain.models import FailureReport, RunSummary
from agentic_qa.domain.statuses import RunStatus
from agentic_qa.failure_analysis.base import FailureAnalyzer


class RuleBasedFailureAnalyzer(FailureAnalyzer):
    ENVIRONMENT_MARKERS = (
        "connection refused",
        "connection error",
        "connecterror",
        "failed to establish a new connection",
        "timed out",
        "timeout",
    )

    def analyze(self, summary: RunSummary, run_dir: Path) -> FailureReport:
        if summary.overall_status == RunStatus.GENERATION_FAILED:
            return FailureReport(
                classification="test_config_error",
                confidence="high",
                explanation="Generation failed before execution, which points to generator or test-configuration setup rather than an application defect.",
                suggested_next_action="Inspect generator inputs and generation exceptions, then fix the broken generation path before rerunning.",
            )

        if self._has_environment_issue(run_dir):
            return FailureReport(
                classification="environment_issue",
                confidence="high",
                explanation="Persisted logs contain connection or timeout markers, which indicate an environment or reachability issue rather than stable application behavior.",
                suggested_next_action="Verify the sample SUT is reachable and rerun after confirming network and process availability.",
            )

        if self._has_real_app_bug(summary):
            return FailureReport(
                classification="real_app_bug",
                confidence="high",
                explanation="Python and Robot execution disagree with a non-zero failing exit code on one path, which indicates a likely real behavioral defect across execution paths.",
                suggested_next_action="Compare the failing path logs and generated tests to the passing path and validate the endpoint behavior against the shared request contract.",
            )

        if self._has_assertion_drift(summary, run_dir):
            return FailureReport(
                classification="assertion_drift",
                confidence="medium",
                explanation="Execution passed, but the persisted generated Python test does not assert every expected response field listed in the request artifact.",
                suggested_next_action="Align generated response assertions with the expected_response_fields contract and rerun the workflow.",
            )

        if summary.overall_status == RunStatus.PASSED and not summary.errors:
            return FailureReport(
                classification="clean",
                confidence="high",
                explanation="All participating execution paths passed and no persisted errors were recorded.",
                suggested_next_action="No corrective action is needed.",
            )

        if summary.overall_status == RunStatus.PARTIAL_SUCCESS:
            return FailureReport(
                classification="flaky_suspect",
                confidence="low",
                explanation="The run ended in partial_success without a deterministic rule match for environment, generation, or cross-path disagreement.",
                suggested_next_action="Review the persisted logs and rerun to confirm whether the failure signal is repeatable.",
            )

        return FailureReport(
            classification="flaky_suspect",
            confidence="low",
            explanation="The run did not match a more specific deterministic failure rule from persisted evidence.",
            suggested_next_action="Review the persisted artifacts manually and rerun to gather a clearer failure signal.",
        )

    def _has_real_app_bug(self, summary: RunSummary) -> bool:
        python_metrics = summary.execution_summary.get("python")
        robot_metrics = summary.execution_summary.get("robot")
        if python_metrics is None or robot_metrics is None:
            return False

        python_failed = python_metrics.status == "failed" and python_metrics.exit_code != 0
        robot_failed = robot_metrics.status == "failed" and robot_metrics.exit_code != 0
        python_passed = python_metrics.status == "passed"
        robot_passed = robot_metrics.status == "passed"
        return (python_passed and robot_failed) or (robot_passed and python_failed)

    def _has_assertion_drift(self, summary: RunSummary, run_dir: Path) -> bool:
        if summary.overall_status != RunStatus.PASSED:
            return False

        request_path = run_dir / "request.json"
        generated_python = run_dir / "generated" / self._generated_python_name(summary)
        if not request_path.exists() or not generated_python.exists():
            return False

        request_payload = json.loads(request_path.read_text(encoding="utf-8"))
        expected_fields = request_payload.get("expected_response_fields", [])
        if not isinstance(expected_fields, list) or not expected_fields:
            return False

        generated_text = generated_python.read_text(encoding="utf-8")
        return any(field not in generated_text for field in expected_fields)

    def _has_environment_issue(self, run_dir: Path) -> bool:
        for path in self._log_candidates(run_dir):
            if not path.exists() or not path.is_file():
                continue
            content = path.read_text(encoding="utf-8", errors="replace").lower()
            if any(marker in content for marker in self.ENVIRONMENT_MARKERS):
                return True
        return False

    @staticmethod
    def _generated_python_name(summary: RunSummary) -> str:
        generated_path = summary.artifacts.get("generated_python_test", "")
        return Path(generated_path).name

    @staticmethod
    def _log_candidates(run_dir: Path) -> list[Path]:
        candidates = list((run_dir / "logs").glob("*.log"))
        browser_dir = run_dir / "browser"
        if browser_dir.exists():
            candidates.extend(browser_dir.glob("*.log"))
            candidates.extend(browser_dir.glob("*.json"))
        return candidates