from pathlib import Path

from agentic_qa.domain.models import ExecutionMetrics, RunSummary
from agentic_qa.domain.statuses import RunStatus
from agentic_qa.failure_analysis.rule_based import RuleBasedFailureAnalyzer


def _summary(
    *,
    overall_status: RunStatus,
    python_status: str = "passed",
    python_exit: int = 0,
    robot_status: str = "passed",
    robot_exit: int = 0,
    errors: list[str] | None = None,
) -> RunSummary:
    return RunSummary(
        run_id="run-001",
        workflow_name="api_feature_validation_v1",
        overall_status=overall_status,
        request_summary={"feature_name": "create widget", "endpoint": "/api/v1/widgets", "method": "POST"},
        plan={"step_count": 7, "generated_files": ["generated/test_api_create_widget.py"]},
        execution_summary={
            "python": ExecutionMetrics(status=python_status, passed=1 if python_status == "passed" else 0, failed=1 if python_status == "failed" else 0, exit_code=python_exit),
            "robot": ExecutionMetrics(status=robot_status, passed=1 if robot_status == "passed" else 0, failed=1 if robot_status == "failed" else 0, exit_code=robot_exit),
        },
        artifacts={"generated_python_test": "generated/test_api_create_widget.py"},
        errors=errors or [],
        started_at="2026-03-27T00:00:00Z",
        finished_at="2026-03-27T00:00:01Z",
    )


def _write_request_and_python(run_dir: Path, *, expected_fields: list[str], generated_python: str) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "generated").mkdir(exist_ok=True)
    (run_dir / "logs").mkdir(exist_ok=True)
    (run_dir / "request.json").write_text(
        '{"expected_response_fields": ' + str(expected_fields).replace("'", '"') + '}',
        encoding="utf-8",
    )
    (run_dir / "generated" / "test_api_create_widget.py").write_text(generated_python, encoding="utf-8")


def test_rule_based_analyzer_classifies_test_config_error(tmp_path) -> None:
    summary = _summary(overall_status=RunStatus.GENERATION_FAILED, python_status="skipped", robot_status="skipped")

    report = RuleBasedFailureAnalyzer().analyze(summary, tmp_path)

    assert report.classification == "test_config_error"
    assert report.confidence == "high"


def test_rule_based_analyzer_classifies_real_app_bug(tmp_path) -> None:
    summary = _summary(overall_status=RunStatus.PARTIAL_SUCCESS, python_status="passed", robot_status="failed", robot_exit=2)

    report = RuleBasedFailureAnalyzer().analyze(summary, tmp_path)

    assert report.classification == "real_app_bug"
    assert report.confidence == "high"


def test_rule_based_analyzer_classifies_environment_issue(tmp_path) -> None:
    summary = _summary(overall_status=RunStatus.FAILED, python_status="failed", python_exit=1, robot_status="failed", robot_exit=1)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs" / "python_execution.log").write_text("ConnectError: connection refused", encoding="utf-8")

    report = RuleBasedFailureAnalyzer().analyze(summary, tmp_path)

    assert report.classification == "environment_issue"
    assert report.confidence == "high"


def test_rule_based_analyzer_classifies_assertion_drift(tmp_path) -> None:
    summary = _summary(overall_status=RunStatus.PASSED)
    _write_request_and_python(
        tmp_path,
        expected_fields=["id", "name", "priority", "status"],
        generated_python="assert 'id' in body\nassert 'name' in body\n",
    )

    report = RuleBasedFailureAnalyzer().analyze(summary, tmp_path)

    assert report.classification == "assertion_drift"
    assert report.confidence == "medium"


def test_rule_based_analyzer_classifies_flaky_suspect(tmp_path) -> None:
    summary = _summary(overall_status=RunStatus.PARTIAL_SUCCESS, python_status="failed", python_exit=0, robot_status="skipped", robot_exit=0)
    (tmp_path / "logs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "logs" / "python_execution.log").write_text("AssertionError: mismatch", encoding="utf-8")

    report = RuleBasedFailureAnalyzer().analyze(summary, tmp_path)

    assert report.classification == "flaky_suspect"
    assert report.confidence == "low"


def test_rule_based_analyzer_classifies_clean(tmp_path) -> None:
    summary = _summary(overall_status=RunStatus.PASSED)
    _write_request_and_python(
        tmp_path,
        expected_fields=["id", "name"],
        generated_python="assert 'id' in body\nassert 'name' in body\n",
    )

    report = RuleBasedFailureAnalyzer().analyze(summary, tmp_path)

    assert report.classification == "clean"
    assert report.confidence == "high"