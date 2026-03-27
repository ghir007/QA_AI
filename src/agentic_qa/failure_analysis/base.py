from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from agentic_qa.domain.models import FailureReport, RunSummary


class FailureAnalyzer(ABC):
    @abstractmethod
    def analyze(self, summary: RunSummary, run_dir: Path) -> FailureReport:
        raise NotImplementedError