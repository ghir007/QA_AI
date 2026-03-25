from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from agentic_qa.config.settings import Settings, get_settings
from agentic_qa.domain.models import FeatureValidationRequest, RunSummary, empty_execution_summary
from agentic_qa.domain.statuses import RunStatus, StepStatus
from agentic_qa.execution.browser_executor import BrowserExecutor, create_browser_executor
from agentic_qa.execution.python_executor import execute_python_test
from agentic_qa.execution.robot_executor import execute_robot_suite
from agentic_qa.generators.browser_generator import build_browser_validation_content
from agentic_qa.generators.python_generator import build_python_test_content
from agentic_qa.generators.robot_generator import build_robot_suite_content
from agentic_qa.observability.logging import logger
from agentic_qa.orchestration.planner import build_run_plan
from agentic_qa.storage.artifact_store import ArtifactStore
from agentic_qa.storage.run_store import RunStore


class SettingsLike(Protocol):
    sample_sut_base_url: str


class RunService:
    ROBOT_RESOURCE_CONTENT = """*** Settings ***
Library    RequestsLibrary

*** Variables ***
${BASE_URL}    http://127.0.0.1:8010
&{VALID_HEADERS}    X-API-Key=demo-key
&{INVALID_HEADERS}    X-API-Key=invalid-key
"""

    def __init__(self, artifact_store: ArtifactStore, run_store: RunStore, settings: SettingsLike, browser_executor: BrowserExecutor | None = None) -> None:
        self.artifact_store = artifact_store
        self.run_store = run_store
        self.settings = settings
        self.browser_executor = browser_executor

    def execute(self, request: FeatureValidationRequest) -> RunSummary:
        started_at = datetime.now(UTC)
        plan = build_run_plan(request, self.artifact_store.root)
        run_dir = self.artifact_store.prepare_run_dir(plan.run_id)
        errors: list[str] = []
        step_index = {step.name: step for step in plan.steps}

        self.artifact_store.write_json(run_dir / "request.json", request.model_dump())
        self.artifact_store.write_json(run_dir / "run_plan.json", plan.model_dump(mode="json"))
        self.artifact_store.write_text(run_dir / "resources" / "common.resource", self.ROBOT_RESOURCE_CONTENT)
        logger.info("run_started", run_id=plan.run_id, feature_name=request.feature_name)

        execution_summary = empty_execution_summary(include_browser=request.enable_browser_validation)
        browser_path: Path | None = None
        artifact_map: dict[str, str] = {
            "plan_json": self.artifact_store.relative_path(run_dir / "run_plan.json"),
        }

        try:
            python_name, python_content = build_python_test_content(request, self.settings.sample_sut_base_url)
            python_path = run_dir / "generated" / python_name
            self.artifact_store.write_text(python_path, python_content)
            artifact_map["generated_python_test"] = self.artifact_store.relative_path(python_path)
            step_index["generate_python_tests"].status = StepStatus.COMPLETED

            robot_name, robot_content = build_robot_suite_content(request)
            robot_path = run_dir / "generated" / robot_name
            self.artifact_store.write_text(robot_path, robot_content)
            artifact_map["generated_robot_suite"] = self.artifact_store.relative_path(robot_path)
            step_index["generate_robot_tests"].status = StepStatus.COMPLETED

            if request.enable_browser_validation:
                browser_name, browser_content = build_browser_validation_content(request, self.settings.sample_sut_base_url)
                browser_path = run_dir / "generated" / browser_name
                self.artifact_store.write_text(browser_path, browser_content)
                artifact_map["generated_browser_validation"] = self.artifact_store.relative_path(browser_path)
                step_index["generate_browser_validation"].status = StepStatus.COMPLETED
                step_index["generate_browser_validation"].detail = "Browser validation artifact generated."
        except Exception as exc:
            errors.append(f"generation failed: {exc}")
            summary = RunSummary(
                run_id=plan.run_id,
                workflow_name=plan.workflow_name,
                overall_status=RunStatus.GENERATION_FAILED,
                request_summary={
                    "feature_name": request.feature_name,
                    "endpoint": request.target_endpoint.path,
                    "method": request.target_endpoint.method.upper(),
                },
                plan={"step_count": len(plan.steps), "generated_files": self._generated_files(artifact_map)},
                execution_summary=execution_summary,
                artifacts=artifact_map,
                errors=errors,
                started_at=started_at,
                finished_at=datetime.now(UTC),
            )
            self._persist_summary(run_dir, summary)
            return summary

        if request.execution_mode in {"both", "python_only"}:
            python_log = run_dir / "logs" / "python_execution.log"
            python_result = execute_python_test(python_path, python_log, run_dir)
            execution_summary["python"] = python_result
            artifact_map["python_log"] = self.artifact_store.relative_path(python_log)
            step_index["execute_python_tests"].status = StepStatus.COMPLETED if python_result.exit_code == 0 else StepStatus.FAILED
        else:
            step_index["execute_python_tests"].status = StepStatus.SKIPPED

        if request.execution_mode in {"both", "robot_only"}:
            robot_log = run_dir / "logs" / "robot_execution.log"
            robot_output_dir = run_dir / "robot"
            robot_result = execute_robot_suite(
                robot_path,
                robot_output_dir,
                robot_log,
                self.settings.sample_sut_base_url,
            )
            execution_summary["robot"] = robot_result
            artifact_map["robot_log"] = self.artifact_store.relative_path(robot_log)
            artifact_map["robot_output_xml"] = self.artifact_store.relative_path(robot_output_dir / "output.xml")
            artifact_map["robot_log_html"] = self.artifact_store.relative_path(robot_output_dir / "log.html")
            artifact_map["robot_report_html"] = self.artifact_store.relative_path(robot_output_dir / "report.html")
            step_index["execute_robot_tests"].status = StepStatus.COMPLETED if robot_result.exit_code == 0 else StepStatus.FAILED
        else:
            step_index["execute_robot_tests"].status = StepStatus.SKIPPED

        if request.enable_browser_validation:
            assert browser_path is not None
            browser_result = (self.browser_executor or create_browser_executor("none")).execute(
                browser_path,
                run_dir,
                self.settings.sample_sut_base_url,
            )
            execution_summary["browser"] = browser_result.metrics
            artifact_map.update(
                {
                    name: self.artifact_store.relative_path(path)
                    for name, path in browser_result.artifacts.items()
                }
            )
            errors.extend(browser_result.errors)
            if browser_result.metrics.status == "passed":
                step_index["execute_browser_validation"].status = StepStatus.COMPLETED
                step_index["execute_browser_validation"].detail = "Browser validation completed."
            elif browser_result.metrics.status == "failed":
                step_index["execute_browser_validation"].status = StepStatus.FAILED
                step_index["execute_browser_validation"].detail = "Browser validation failed."
            else:
                step_index["execute_browser_validation"].status = StepStatus.SKIPPED
                step_index["execute_browser_validation"].detail = "Browser validation was requested but no executor was available."

        overall_status = self._determine_status(
            execution_summary["python"].status,
            execution_summary["robot"].status,
            request.execution_mode,
            browser_status=execution_summary["browser"].status if request.enable_browser_validation else None,
        )
        summary = RunSummary(
            run_id=plan.run_id,
            workflow_name=plan.workflow_name,
            overall_status=overall_status,
            request_summary={
                "feature_name": request.feature_name,
                "endpoint": request.target_endpoint.path,
                "method": request.target_endpoint.method.upper(),
            },
            plan={
                "step_count": len(plan.steps),
                "generated_files": self._generated_files(artifact_map),
            },
            execution_summary=execution_summary,
            artifacts=artifact_map,
            errors=errors,
            started_at=started_at,
            finished_at=datetime.now(UTC),
        )
        self._persist_summary(run_dir, summary)
        logger.info("run_completed", run_id=plan.run_id, overall_status=summary.overall_status)
        return summary

    def get(self, run_id: str) -> RunSummary | None:
        cached = self.run_store.get(run_id)
        if cached is not None:
            return RunSummary.model_validate(cached)

        stored = self.artifact_store.get_run_summary(run_id)
        if stored is None:
            return None
        self.run_store.save(run_id, stored)
        return RunSummary.model_validate(stored)

    def _persist_summary(self, run_dir: Path, summary: RunSummary) -> None:
        self.artifact_store.write_json(run_dir / "summary.json", summary.model_dump(mode="json"))
        self.run_store.save(summary.run_id, summary.model_dump(mode="json"))

    @staticmethod
    def _generated_files(artifact_map: dict[str, str]) -> list[str]:
        return [
            artifact_map[key]
            for key in ("generated_python_test", "generated_robot_suite", "generated_browser_validation")
            if key in artifact_map
        ]

    @staticmethod
    def _determine_status(
        python_status: str,
        robot_status: str,
        execution_mode: str,
        browser_status: str | None = None,
    ) -> RunStatus:
        statuses = []
        if execution_mode in {"both", "python_only"}:
            statuses.append(python_status)
        if execution_mode in {"both", "robot_only"}:
            statuses.append(robot_status)
        if browser_status is not None:
            statuses.append(browser_status)

        if statuses and all(status == "passed" for status in statuses):
            return RunStatus.PASSED
        if statuses and all(status == "failed" for status in statuses):
            return RunStatus.FAILED
        return RunStatus.PARTIAL_SUCCESS


def create_run_service() -> RunService:
    settings = get_settings()
    artifact_store = ArtifactStore(settings.artifact_root)
    run_store = RunStore()
    browser_executor = create_browser_executor(
        settings.browser_executor,
        fake_outcome=settings.browser_fake_outcome,
        mcp_endpoint=settings.mcp_browser_endpoint,
        mcp_timeout_seconds=settings.mcp_browser_timeout_seconds,
    )
    return RunService(artifact_store=artifact_store, run_store=run_store, settings=settings, browser_executor=browser_executor)