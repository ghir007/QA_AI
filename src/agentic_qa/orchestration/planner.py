from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from agentic_qa.domain.models import FeatureValidationRequest, RunPlan, RunStep


def build_run_plan(request: FeatureValidationRequest, artifact_root: Path) -> RunPlan:
    run_id = str(uuid4())
    steps = [
        RunStep(name="plan_request"),
        RunStep(name="generate_python_tests"),
        RunStep(name="generate_robot_tests"),
    ]

    if request.enable_browser_validation:
        steps.append(RunStep(name="generate_browser_validation"))

    steps.extend([
        RunStep(name="execute_python_tests"),
        RunStep(name="execute_robot_tests"),
    ])

    if request.enable_browser_validation:
        steps.append(RunStep(name="execute_browser_validation"))

    steps.extend([
        RunStep(name="collect_artifacts"),
        RunStep(name="build_summary"),
    ])
    return RunPlan(run_id=run_id, request_snapshot=request, steps=steps, artifact_root=str(artifact_root / run_id))