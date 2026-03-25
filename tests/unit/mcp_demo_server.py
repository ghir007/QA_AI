from __future__ import annotations

import base64
import json
import os
import sys
import time


ONE_PIXEL_PNG = bytes.fromhex(
    "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C489"
    "0000000D49444154789C6360000002000154A24F5D0000000049454E44AE426082"
)


def _read_message() -> dict:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            raise EOFError
        if line in {b"\n", b"\r\n"}:
            break
        name, value = line.decode("ascii").split(":", 1)
        headers[name.strip().lower()] = value.strip()

    length = int(headers["content-length"])
    body = sys.stdin.buffer.read(length)
    return json.loads(body.decode("utf-8"))


def _write_message(payload: dict) -> None:
    body = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body)
    sys.stdout.buffer.flush()


def _write_raw_message(header: str, body: bytes) -> None:
    sys.stdout.buffer.write(header.encode("ascii") + body)
    sys.stdout.buffer.flush()


def main() -> int:
    mode = os.environ.get("MCP_DEMO_MODE", "passed")
    while True:
        try:
            message = _read_message()
        except EOFError:
            return 0

        method = message.get("method")
        if method == "initialize":
            if mode == "hang":
                time.sleep(60)
            _write_message(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "demo-mcp-browser", "version": "0.1.0"},
                    },
                }
            )
        elif method == "notifications/initialized":
            continue
        elif method == "tools/call":
            validation = message["params"]["arguments"]["validation"]
            if mode == "protocol_error":
                _write_message(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "error": {"code": -32000, "message": "browser tool failed"},
                    }
                )
                continue

            if mode == "invalid_content_length":
                body = json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": message["id"],
                        "result": {"structuredContent": {"success": True, "message": "ignored"}},
                    }
                ).encode("utf-8")
                _write_raw_message("Content-Length: nope\r\n\r\n", body)
                continue

            if mode == "notify_first":
                _write_message(
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/message",
                        "params": {"level": "info", "message": "about to respond"},
                    }
                )

            success = mode != "failed"
            artifacts = {
                "browser_screenshot_base64": base64.b64encode(ONE_PIXEL_PNG).decode("ascii"),
                "browser_result_json": {
                    "status": "passed" if success else "failed",
                    "page_path": validation["page_path"],
                    "expected_result_text": validation["expected"]["result_text"],
                },
            }
            if mode == "invalid_artifact":
                artifacts["browser_screenshot_base64"] = "not-base64"
            if mode == "invalid_result_json":
                artifacts["browser_result_json"] = '{"status": "passed"'

            structured_content: object = {
                "success": success,
                "message": "browser validation complete",
                "artifacts": artifacts,
            }
            if mode == "non_dict_structured_content":
                structured_content = ["not-an-object"]

            _write_message(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "result": {
                        "content": [{"type": "text", "text": "browser validation complete"}],
                        "structuredContent": structured_content,
                    },
                }
            )
        else:
            _write_message(
                {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "error": {"code": -32601, "message": f"Unsupported method: {method}"},
                }
            )


if __name__ == "__main__":
    raise SystemExit(main())