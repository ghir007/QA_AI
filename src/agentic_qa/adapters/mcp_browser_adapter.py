from __future__ import annotations

import base64
import binascii
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MCPBrowserExecutionResponse:
    available: bool
    success: bool
    stdout: str = ""
    stderr: str = ""
    artifacts: dict[str, bytes | str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class MCPBrowserAdapter:
    """Narrow boundary for future MCP-backed browser execution."""

    def __init__(
        self,
        command: str | None,
        args: list[str] | None = None,
        tool_name: str = "browser_validate_ui",
        timeout_seconds: float = 5.0,
    ) -> None:
        self.command = command
        self.args = args or []
        self.tool_name = tool_name
        self.timeout_seconds = timeout_seconds

    def is_available(self) -> bool:
        return bool(self.command)

    def execute_validation(self, script_path: Path, base_url: str) -> MCPBrowserExecutionResponse:
        if not self.is_available():
            return MCPBrowserExecutionResponse(
                available=False,
                success=False,
                stderr="MCP browser command is not configured.",
                metadata={"script_path": str(script_path), "base_url": base_url},
            )

        command = self.command
        assert command is not None

        try:
            raw_validation = script_path.read_text(encoding="utf-8")
        except OSError as exc:
            return MCPBrowserExecutionResponse(
                available=False,
                success=False,
                stderr=f"Failed to read MCP browser validation artifact: {exc}",
                metadata={"script_path": str(script_path), "base_url": base_url},
            )

        try:
            validation = json.loads(raw_validation)
        except json.JSONDecodeError as exc:
            return MCPBrowserExecutionResponse(
                available=False,
                success=False,
                stderr=f"MCP browser validation artifact was malformed JSON: {exc}",
                metadata={"script_path": str(script_path), "base_url": base_url},
            )

        try:
            process = subprocess.Popen(
                [command, *self.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            return MCPBrowserExecutionResponse(
                available=False,
                success=False,
                stderr=f"Failed to start MCP browser command: {exc}",
                metadata={"script_path": str(script_path), "base_url": base_url, "command": self.command},
            )

        stderr = ""
        try:
            messages, stderr = self._exchange_messages(
                process,
                [
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "agentic-qa-copilot", "version": "0.1.0"},
                        },
                    },
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized",
                        "params": {},
                    },
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {
                            "name": self.tool_name,
                            "arguments": {
                                "validation": validation,
                                "base_url": base_url,
                            },
                        },
                    },
                ],
            )
            initialize_response = self._extract_response(messages, 1)
            tool_response = self._extract_response(messages, 2)
            structured = tool_response.get("structuredContent") or {}
            if not isinstance(structured, dict):
                raise RuntimeError("MCP tool response structuredContent was not an object")
            artifacts = self._normalize_artifacts(structured.get("artifacts", {}))
            raw_message = structured.get("message")
            message = raw_message if isinstance(raw_message, str) else ""
        except (RuntimeError, json.JSONDecodeError, binascii.Error, UnicodeDecodeError) as exc:
            return MCPBrowserExecutionResponse(
                available=False,
                success=False,
                stderr=f"MCP browser execution failed: {exc}. {stderr}".strip(),
                metadata={"script_path": str(script_path), "base_url": base_url, "command": command},
            )

        return MCPBrowserExecutionResponse(
            available=True,
            success=bool(structured.get("success", False)),
            stdout=message,
            stderr=stderr,
            artifacts=artifacts,
            metadata={
                "script_path": str(script_path),
                "base_url": base_url,
                "command": command,
                "tool_name": self.tool_name,
            },
        )

    @staticmethod
    def _encode_message(payload: dict[str, Any]) -> bytes:
        body = json.dumps(payload).encode("utf-8")
        header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
        return header + body

    def _exchange_messages(self, process: subprocess.Popen, payloads: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
        request_bytes = b"".join(self._encode_message(payload) for payload in payloads)
        try:
            stdout, stderr = process.communicate(input=request_bytes, timeout=self.timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            stdout, stderr = process.communicate()
            raise RuntimeError(f"MCP browser execution timed out after {self.timeout_seconds} seconds") from exc

        return self._parse_messages(stdout), stderr.decode("utf-8", errors="replace").strip()

    @staticmethod
    def _parse_messages(stdout: bytes) -> list[dict[str, Any]]:
        if not stdout:
            raise RuntimeError("MCP server produced no stdout output")

        messages: list[dict[str, Any]] = []
        index = 0
        total_length = len(stdout)
        while index < total_length:
            header_end = stdout.find(b"\r\n\r\n", index)
            if header_end == -1:
                raise RuntimeError("MCP response missing header terminator")

            try:
                raw_headers = stdout[index:header_end].decode("ascii")
            except UnicodeDecodeError as exc:
                raise RuntimeError("MCP response headers were not ASCII") from exc

            headers: dict[str, str] = {}
            for line in raw_headers.split("\r\n"):
                if ":" not in line:
                    raise RuntimeError("MCP response header line was malformed")
                name, value = line.split(":", 1)
                headers[name.strip().lower()] = value.strip()

            body_start = header_end + 4
            try:
                body_length = int(headers.get("content-length", "0"))
            except ValueError as exc:
                raise RuntimeError("MCP response content-length was invalid") from exc
            if body_length <= 0:
                raise RuntimeError("MCP response missing content-length")

            body_end = body_start + body_length
            if body_end > total_length:
                raise RuntimeError("MCP response body was truncated")

            message = json.loads(stdout[body_start:body_end].decode("utf-8"))
            if not isinstance(message, dict):
                raise RuntimeError("MCP response body was not an object")
            messages.append(message)
            index = body_end

        return messages

    @staticmethod
    def _extract_response(messages: list[dict[str, Any]], request_id: int) -> dict[str, Any]:
        for message in messages:
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise RuntimeError(str(message["error"]))
            return message.get("result", {})
        raise RuntimeError(f"No MCP response received for request id {request_id}")

    @staticmethod
    def _normalize_artifacts(raw_artifacts: dict[str, Any]) -> dict[str, bytes | str]:
        if not isinstance(raw_artifacts, dict):
            raise RuntimeError("MCP tool response artifacts field was not an object")

        normalized: dict[str, bytes | str] = {}
        screenshot_base64 = raw_artifacts.get("browser_screenshot_base64")
        if isinstance(screenshot_base64, str):
            normalized["browser_screenshot"] = base64.b64decode(screenshot_base64)

        result_json = raw_artifacts.get("browser_result_json")
        if isinstance(result_json, dict):
            normalized["browser_result_json"] = json.dumps(result_json, indent=2)
        elif isinstance(result_json, str):
            normalized["browser_result_json"] = result_json

        trace_json = raw_artifacts.get("browser_trace_json")
        if isinstance(trace_json, dict):
            normalized["browser_trace_json"] = json.dumps(trace_json, indent=2)
        elif isinstance(trace_json, str):
            normalized["browser_trace_json"] = trace_json

        return normalized