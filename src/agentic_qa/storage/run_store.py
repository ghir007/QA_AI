from __future__ import annotations

from collections.abc import Mapping


class RunStore:
    def __init__(self) -> None:
        self._runs: dict[str, dict] = {}

    def save(self, run_id: str, summary: Mapping[str, object]) -> None:
        self._runs[run_id] = dict(summary)

    def get(self, run_id: str) -> dict | None:
        return self._runs.get(run_id)