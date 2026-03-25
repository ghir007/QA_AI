from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from agentic_qa.domain.models import ExecutionMetrics


def execute_python_test(test_file: Path, log_file: Path, working_directory: Path) -> ExecutionMetrics:
    command = [sys.executable, "-m", "pytest", str(test_file), "-q"]
    result = subprocess.run(
        command,
        cwd=working_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    log_content = f"COMMAND: {' '.join(command)}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
    log_file.write_text(log_content, encoding="utf-8")

    passed_match = re.search(r"(\d+) passed", result.stdout)
    failed_match = re.search(r"(\d+) failed", result.stdout)
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    status = "passed" if result.returncode == 0 else "failed"
    return ExecutionMetrics(status=status, passed=passed, failed=failed, exit_code=result.returncode)