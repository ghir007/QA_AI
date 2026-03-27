from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from agentic_qa.domain.models import FailureReport, RemediationPlan, RunSummary


class RemediationAdvisor(ABC):
    @abstractmethod
    def build_plan(self, failure_report: FailureReport, summary: RunSummary, run_dir: Path) -> RemediationPlan:
        raise NotImplementedError