from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from agentic_qa.domain.models import ExecutionMetrics


def execute_robot_suite(
    suite_file: Path,
    output_dir: Path,
    log_file: Path,
    base_url: str,
) -> ExecutionMetrics:
    command = [
        sys.executable,
        "-m",
        "robot",
        "--variable",
        f"BASE_URL:{base_url}",
        "--outputdir",
        str(output_dir),
        str(suite_file),
    ]
    result = subprocess.run(
        command,
        cwd=output_dir.parent,
        capture_output=True,
        text=True,
        check=False,
    )
    log_content = f"COMMAND: {' '.join(command)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    log_file.write_text(log_content, encoding="utf-8")

    passed_match = re.search(r"(\d+) test[s]?, (\d+) passed, (\d+) failed", result.stdout, re.IGNORECASE)
    if passed_match:
        passed = int(passed_match.group(2))
        failed = int(passed_match.group(3))
    else:
        passed = 0
        failed = 0 if result.returncode == 0 else 1

    status = "passed" if result.returncode == 0 else "failed"
    return ExecutionMetrics(status=status, passed=passed, failed=failed, exit_code=result.returncode)