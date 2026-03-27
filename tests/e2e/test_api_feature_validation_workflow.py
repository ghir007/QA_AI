from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

from agentic_qa.main import create_app


def _wait_for_port(host: str, port: int, timeout: float = 10.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {host}:{port}")


def test_api_feature_validation_happy_path(tmp_path) -> None:
    os.environ["ARTIFACT_ROOT"] = str(tmp_path / "runs")
    os.environ["SAMPLE_SUT_BASE_URL"] = "http://127.0.0.1:8010"
    env = os.environ.copy()
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "sample_sut.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8010",
        ],
        env=env,
    )

    try:
        _wait_for_port("127.0.0.1", 8010)
        client = TestClient(create_app())
        payload = {
            "request_id": "req-001",
            "feature_name": "create widget",
            "feature_description": "validate widget creation",
            "target_endpoint": {"path": "/api/v1/widgets", "method": "POST"},
            "expected_status_code": 201,
            "request_payload_example": {"name": "smoke-widget", "priority": "high"},
            "expected_response_fields": ["id", "name", "priority", "status"],
            "negative_cases": ["invalid_auth"],
            "execution_mode": "both",
            "tags": ["smoke"],
        }

        response = client.post("/runs", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["overall_status"] == "passed"
        assert body["execution_summary"]["python"]["status"] == "passed"
        assert body["execution_summary"]["robot"]["status"] == "passed"
        assert "browser" not in body["execution_summary"]
        assert Path(tmp_path / "runs" / body["artifacts"]["plan_json"]).exists()
        assert Path(tmp_path / "runs" / body["artifacts"]["generated_python_test"]).exists()
        assert Path(tmp_path / "runs" / body["artifacts"]["generated_robot_suite"]).exists()
        get_response = client.get(f"/runs/{body['run_id']}")
        assert get_response.status_code == 200
        assert get_response.json() == body
    finally:
        server.terminate()
        server.wait(timeout=10)


def test_api_feature_validation_browser_requested_marks_partial_success(tmp_path) -> None:
    os.environ["ARTIFACT_ROOT"] = str(tmp_path / "runs")
    os.environ["SAMPLE_SUT_BASE_URL"] = "http://127.0.0.1:8010"
    env = os.environ.copy()
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "sample_sut.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8010",
        ],
        env=env,
    )

    try:
        _wait_for_port("127.0.0.1", 8010)
        client = TestClient(create_app())
        payload = {
            "request_id": "req-002",
            "feature_name": "create widget",
            "feature_description": "validate widget creation in browser",
            "target_endpoint": {"path": "/api/v1/widgets", "method": "POST"},
            "expected_status_code": 201,
            "request_payload_example": {"name": "browser-widget", "priority": "normal"},
            "expected_response_fields": ["id", "name", "priority", "status"],
            "negative_cases": [],
            "execution_mode": "both",
            "enable_browser_validation": True,
            "tags": ["browser"],
        }

        response = client.post("/runs", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["overall_status"] == "passed"
        assert body["execution_summary"]["python"]["status"] == "passed"
        assert body["execution_summary"]["robot"]["status"] == "passed"
        assert body["execution_summary"]["browser"]["status"] == "skipped"
        assert Path(tmp_path / "runs" / body["artifacts"]["generated_browser_validation"]).exists()
        assert Path(tmp_path / "runs" / body["artifacts"]["browser_log"]).exists()
        assert any("browser executor is not configured" in error for error in body["errors"])
    finally:
        server.terminate()
        server.wait(timeout=10)


def test_release_readiness_returns_summary_when_enabled(tmp_path) -> None:
    os.environ["ARTIFACT_ROOT"] = str(tmp_path / "runs")
    os.environ["SAMPLE_SUT_BASE_URL"] = "http://127.0.0.1:8010"
    os.environ["ENABLE_RELEASE_ORCHESTRATION"] = "true"
    env = os.environ.copy()
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "sample_sut.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8010",
        ],
        env=env,
    )

    try:
        _wait_for_port("127.0.0.1", 8010)
        client = TestClient(create_app())
        payload = {
            "request_id": "req-release-001",
            "feature_name": "create widget",
            "feature_description": "validate widget creation",
            "target_endpoint": {"path": "/api/v1/widgets", "method": "POST"},
            "expected_status_code": 201,
            "request_payload_example": {"name": "smoke-widget", "priority": "high"},
            "expected_response_fields": ["id", "name", "priority", "status"],
            "negative_cases": ["invalid_auth"],
            "execution_mode": "both",
            "tags": ["smoke"],
        }

        run_response = client.post("/runs", json=payload)
        assert run_response.status_code == 200
        run_body = run_response.json()

        readiness_response = client.get(f"/release-readiness?run_ids={run_body['run_id']}")
        assert readiness_response.status_code == 200
        readiness_body = readiness_response.json()
        assert readiness_body["total_requests"] == 1
        assert readiness_body["scored_requests"][0]["request_id"] == "req-release-001"
        assert readiness_body["recommended_suite"] in {"smoke_only", "regression_subset", "full_suite"}
    finally:
        server.terminate()
        server.wait(timeout=10)
        os.environ.pop("ENABLE_RELEASE_ORCHESTRATION", None)


def test_release_readiness_returns_404_when_disabled(tmp_path) -> None:
    os.environ["ARTIFACT_ROOT"] = str(tmp_path / "runs")
    os.environ["SAMPLE_SUT_BASE_URL"] = "http://127.0.0.1:8010"
    os.environ.pop("ENABLE_RELEASE_ORCHESTRATION", None)

    client = TestClient(create_app())
    response = client.get("/release-readiness?run_ids=missing-run")

    assert response.status_code == 404
    assert response.json()["detail"] == "release orchestration is disabled"