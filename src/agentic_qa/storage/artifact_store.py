from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def prepare_run_dir(self, run_id: str) -> Path:
        run_dir = self.root / run_id
        for directory in [run_dir, run_dir / "generated", run_dir / "logs", run_dir / "robot", run_dir / "resources", run_dir / "browser"]:
            directory.mkdir(parents=True, exist_ok=True)
        return run_dir

    def write_json(self, path: Path, payload: dict[str, Any]) -> Path:
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return path

    def write_text(self, path: Path, content: str) -> Path:
        path.write_text(content, encoding="utf-8")
        return path

    def read_json(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def summary_path(self, run_id: str) -> Path:
        return self.root / run_id / "summary.json"

    def get_run_summary(self, run_id: str) -> dict[str, Any] | None:
        summary_path = self.summary_path(run_id)
        if not summary_path.exists():
            return None
        return self.read_json(summary_path)

    def relative_path(self, path: Path) -> str:
        return path.resolve().relative_to(self.root).as_posix()