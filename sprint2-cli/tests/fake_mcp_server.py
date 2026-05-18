"""Tiny MCP filesystem server used by tests.

It only implements the subset of tools that the Week 1 CLI needs, and it can
use either JSONL or Content-Length stdio framing so protocol tests cover both
supported client modes.
"""

from __future__ import annotations

import fnmatch
import json
import shutil
import sys
from pathlib import Path
from typing import Any, BinaryIO


FRAMING = "content-length" if "--content-length" in sys.argv else "jsonl"
REQUEST_ROOTS = "--request-roots" in sys.argv


def read_content_length_message(stream: BinaryIO) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, value = line.decode("ascii").split(":", 1)
        headers[name.lower()] = value.strip()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    return json.loads(stream.read(length).decode("utf-8"))


def write_content_length_message(stream: BinaryIO, message: dict[str, Any]) -> None:
    body = json.dumps(message, separators=(",", ":")).encode("utf-8")
    stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    stream.write(body)
    stream.flush()


def read_jsonl_message(stream: BinaryIO) -> dict[str, Any] | None:
    line = stream.readline()
    if not line:
        return None
    return json.loads(line.decode("utf-8"))


def write_jsonl_message(stream: BinaryIO, message: dict[str, Any]) -> None:
    stream.write((json.dumps(message, separators=(",", ":")) + "\n").encode("utf-8"))
    stream.flush()


def read_message(stream: BinaryIO) -> dict[str, Any] | None:
    if FRAMING == "content-length":
        return read_content_length_message(stream)
    return read_jsonl_message(stream)


def write_message(stream: BinaryIO, message: dict[str, Any]) -> None:
    if FRAMING == "content-length":
        write_content_length_message(stream, message)
    else:
        write_jsonl_message(stream, message)


def content(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def success(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def failure(request_id: Any, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32000, "message": message}}


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    if name == "list_directory":
        path = Path(args["path"]).resolve()
        if not path.exists():
            raise ValueError(f"Directory not found: {path}")
        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        lines = []
        for child in sorted(path.iterdir(), key=lambda p: p.name):
            prefix = "[DIR]" if child.is_dir() else "[FILE]"
            lines.append(f"{prefix} {child.name}")
        return content("\n".join(lines))

    if name == "search_files":
        path = Path(args["path"]).resolve()
        pattern = args["pattern"]
        if not path.exists():
            raise ValueError(f"Directory not found: {path}")
        matches = [
            str(child)
            for child in sorted(path.rglob("*"))
            if child.is_file() and fnmatch.fnmatch(child.name, pattern)
        ]
        return content("\n".join(matches))

    if name == "get_file_info":
        path = Path(args["path"]).resolve()
        if not path.exists():
            raise ValueError(f"File not found: {path}")
        return content(
            "\n".join(
                [
                    f"Path: {path}",
                    f"Size: {path.stat().st_size}",
                    f"Directory: {path.is_dir()}",
                    f"Modified: {path.stat().st_mtime}",
                ]
            )
        )

    if name == "read_file":
        path = Path(args["path"]).resolve()
        if not path.exists():
            raise ValueError(f"File not found: {path}")
        if path.is_dir():
            raise ValueError(f"Path is a directory: {path}")
        return content(path.read_text(encoding="utf-8"))

    if name == "write_file":
        path = Path(args["path"]).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
        return content(f"Wrote {path}")

    if name == "move_file":
        source = Path(args["source"]).resolve()
        destination = Path(args["destination"]).resolve()
        if not source.exists():
            raise ValueError(f"Source not found: {source}")
        if destination.exists():
            raise ValueError(f"Destination already exists: {destination}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))
        return content(f"Moved {source} to {destination}")

    raise ValueError(f"Unknown tool: {name}")


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    request_id = message.get("id")
    method = message.get("method")
    params = message.get("params") or {}

    if method == "notifications/initialized":
        return None

    try:
        if method == "initialize":
            return success(
                request_id,
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "fake-filesystem-mcp", "version": "0.1.0"},
                },
            )
        if method == "tools/list":
            return success(
                request_id,
                {
                    "tools": [
                        {"name": "list_directory"},
                        {"name": "search_files"},
                        {"name": "get_file_info"},
                        {"name": "read_file"},
                        {"name": "write_file"},
                        {"name": "move_file"},
                    ]
                },
            )
        if method == "tools/call":
            return success(request_id, call_tool(params["name"], params.get("arguments") or {}))
        return failure(request_id, f"Unsupported method: {method}")
    except Exception as exc:
        return failure(request_id, str(exc))


def main() -> None:
    while True:
        message = read_message(sys.stdin.buffer)
        if message is None:
            return
        if REQUEST_ROOTS and message.get("method") == "tools/call":
            write_message(
                sys.stdout.buffer,
                {"jsonrpc": "2.0", "id": 999, "method": "roots/list"},
            )
            roots_response = read_message(sys.stdin.buffer)
            if not roots_response or roots_response.get("id") != 999:
                write_message(sys.stdout.buffer, failure(message.get("id"), "Client did not answer roots/list"))
                continue
        response = handle(message)
        if response is not None:
            write_message(sys.stdout.buffer, response)


if __name__ == "__main__":
    main()
