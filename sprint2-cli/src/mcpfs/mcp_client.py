"""MCP Client — Communicates with MCP filesystem server via stdio transport.

The Model Context Protocol (MCP) uses JSON-RPC 2.0 over stdio to communicate
between a client (this tool) and a server (the filesystem server). The protocol
flow is:

1. Client sends `initialize` request with protocol version and capabilities
2. Server responds with its capabilities and supported tools
3. Client sends `initialized` notification
4. Client can then call tools via `tools/call` requests
5. Client sends shutdown when done

This module abstracts all protocol details behind a clean async interface.
"""

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


class MCPError(Exception):
    """Base exception for MCP protocol errors."""

    def __init__(self, message: str, suggestion: str = ""):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


class MCPConnectionError(MCPError):
    """Raised when unable to connect to MCP server."""
    pass


class MCPToolError(MCPError):
    """Raised when an MCP tool call fails."""
    pass


@dataclass
class MCPClient:
    """Client for communicating with an MCP filesystem server via stdio.

    Manages the subprocess lifecycle and JSON-RPC message exchange.
    """

    server_command: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    framing: str = "jsonl"
    request_timeout: float = 30.0
    _process: Optional[asyncio.subprocess.Process] = field(default=None, init=False)
    _request_id: int = field(default=0, init=False)
    _initialized: bool = field(default=False, init=False)

    def _next_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id

    async def connect(self) -> None:
        """Start the MCP server subprocess and initialize the protocol."""
        try:
            self._process = await asyncio.create_subprocess_exec(
                *self.server_command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            raise MCPConnectionError(
                f"Cannot find MCP server command: {self.server_command[0]}",
                suggestion="Ensure the MCP server is installed. "
                "For the filesystem server: npm install -g @modelcontextprotocol/server-filesystem",
            )
        except PermissionError:
            raise MCPConnectionError(
                f"Permission denied executing: {self.server_command[0]}",
                suggestion="Check that the server binary has execute permissions.",
            )
        except Exception as e:
            raise MCPConnectionError(
                f"Failed to start MCP server: {str(e)}",
                suggestion="Verify the server command is correct and all dependencies are installed.",
            )

        if self.framing not in {"jsonl", "content-length"}:
            raise MCPConnectionError(
                f"Unsupported MCP stdio framing: {self.framing}",
                suggestion="Use 'jsonl' for the official JS SDK server or 'content-length' for header-framed servers.",
            )

        # Send initialize request
        await self._initialize()

    async def _initialize(self) -> None:
        """Perform MCP protocol initialization handshake."""
        response = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
            },
            "clientInfo": {
                "name": "mcpfs",
                "version": "1.0.0",
            },
        })

        if "error" in response:
            raise MCPConnectionError(
                "MCP server rejected initialization",
                suggestion="Server may be incompatible. Expected protocol version 2024-11-05.",
            )

        # Send initialized notification
        await self._send_notification("notifications/initialized", {})
        self._initialized = True

    async def _send_request(self, method: str, params: dict) -> dict:
        """Send a JSON-RPC request and wait for response."""
        if self._process is None or self._process.stdin is None:
            raise MCPConnectionError(
                "Not connected to MCP server",
                suggestion="Call connect() before making requests.",
            )

        request_id = self._next_id()
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params,
        }

        await self._write_message(message)

        deadline = asyncio.get_running_loop().time() + self.request_timeout
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise MCPConnectionError(
                    f"MCP server did not respond within {self.request_timeout:g} seconds",
                    suggestion="The server may be unresponsive. Try restarting it.",
                )

            try:
                response = await asyncio.wait_for(self._read_message(), timeout=remaining)
            except asyncio.TimeoutError:
                raise MCPConnectionError(
                    f"MCP server did not respond within {self.request_timeout:g} seconds",
                    suggestion="The server may be unresponsive. Try restarting it.",
                )

            if response.get("id") == request_id:
                return response

            if "method" in response and "id" in response:
                await self._handle_server_request(response)
                continue

            # Ignore notifications and unrelated responses while waiting for
            # this request. The official filesystem server may send its own
            # requests such as roots/list before returning a tool result.

    async def _write_message(self, message: dict) -> None:
        """Write one MCP stdio message."""
        if self._process is None or self._process.stdin is None:
            raise MCPConnectionError(
                "Not connected to MCP server",
                suggestion="Call connect() before making requests.",
            )

        if self.framing == "content-length":
            body = json.dumps(message, separators=(",", ":")).encode("utf-8")
            header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
            self._process.stdin.write(header + body)
        else:
            line = json.dumps(message, separators=(",", ":")) + "\n"
            self._process.stdin.write(line.encode("utf-8"))
        await self._process.stdin.drain()

    async def _read_message(self) -> dict:
        """Read one MCP stdio message."""
        if self.framing == "content-length":
            return await self._read_content_length_message()
        return await self._read_jsonl_message()

    async def _read_jsonl_message(self) -> dict:
        """Read one newline-delimited JSON-RPC message."""
        if self._process is None or self._process.stdout is None:
            raise MCPConnectionError(
                "Not connected to MCP server",
                suggestion="Call connect() before making requests.",
            )

        line = await self._process.stdout.readline()
        if not line:
            raise MCPConnectionError(
                "MCP server closed connection unexpectedly",
                suggestion="Check server logs for errors. The server process may have crashed.",
            )

        try:
            return json.loads(line.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise MCPConnectionError(
                "MCP server returned invalid JSON",
                suggestion="Server may be sending non-protocol output on stdout. Check stderr.",
            ) from exc

    async def _read_content_length_message(self) -> dict:
        """Read one Content-Length-framed JSON-RPC message."""
        if self._process is None or self._process.stdout is None:
            raise MCPConnectionError(
                "Not connected to MCP server",
                suggestion="Call connect() before making requests.",
            )

        headers: dict[str, str] = {}
        while True:
            line = await self._process.stdout.readline()
            if not line:
                raise MCPConnectionError(
                    "MCP server closed connection unexpectedly",
                    suggestion="Check server logs for errors. The server process may have crashed.",
                )
            if line in (b"\r\n", b"\n"):
                break
            try:
                name, value = line.decode("ascii").split(":", 1)
            except ValueError as exc:
                raise MCPConnectionError(
                    "MCP server returned malformed headers",
                    suggestion="Server may not be using MCP Content-Length framing.",
                ) from exc
            headers[name.lower()] = value.strip()

        try:
            content_length = int(headers["content-length"])
        except (KeyError, ValueError) as exc:
            raise MCPConnectionError(
                "MCP server response did not include a valid Content-Length header",
                suggestion="Verify that the server speaks MCP over stdio.",
            ) from exc

        try:
            raw_body = await self._process.stdout.readexactly(content_length)
        except asyncio.IncompleteReadError as exc:
            raise MCPConnectionError(
                "MCP server closed connection before sending the full response",
                suggestion="Check server logs for protocol or runtime errors.",
            ) from exc

        try:
            return json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise MCPConnectionError(
                "MCP server returned invalid JSON",
                suggestion="Server may be sending non-protocol output on stdout. Check stderr.",
            ) from exc

    async def _send_notification(self, method: str, params: dict) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if self._process is None or self._process.stdin is None:
            return

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        await self._write_message(message)

    async def _handle_server_request(self, message: dict) -> None:
        """Handle JSON-RPC requests sent by the MCP server."""
        request_id = message.get("id")
        method = message.get("method")

        if method == "roots/list":
            roots = []
            for root in self.allowed_paths:
                try:
                    root_uri = Path(root).resolve().as_uri()
                except ValueError:
                    continue
                roots.append({"uri": root_uri, "name": str(Path(root).resolve())})
            await self._write_message({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"roots": roots},
            })
            return

        await self._write_message({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Unsupported client method: {method}",
            },
        })

    async def call_tool(self, tool_name: str, arguments: dict) -> Any:
        """Call an MCP tool and return the result.

        Args:
            tool_name: Name of the tool to call (e.g., 'read_file')
            arguments: Tool-specific arguments

        Returns:
            The tool's result content

        Raises:
            MCPToolError: If the tool call fails
        """
        if not self._initialized:
            raise MCPConnectionError(
                "MCP client not initialized",
                suggestion="Call connect() before calling tools.",
            )

        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })

        if "error" in response:
            error = response["error"]
            raise MCPToolError(
                f"Tool '{tool_name}' failed: {error.get('message', 'Unknown error')}",
                suggestion=self._suggest_fix(tool_name, error),
            )

        result = response.get("result", {})
        if result.get("isError"):
            content = result.get("content", [{}])
            error_text = content[0].get("text", "Unknown error") if content else "Unknown error"
            raise MCPToolError(
                f"Tool '{tool_name}' returned error: {error_text}",
                suggestion=self._suggest_fix(tool_name, {"message": error_text}),
            )

        return result.get("content", [])

    def _suggest_fix(self, tool_name: str, error: dict) -> str:
        """Generate actionable suggestion based on error context."""
        msg = error.get("message", "").lower()

        if "permission" in msg or "access" in msg:
            return "Check file permissions. The MCP server may not have access to this path."
        if "not found" in msg or "no such" in msg:
            return "Verify the file path exists. Use 'mcpfs tree' to explore available files."
        if "already exists" in msg:
            return "The target file already exists. Use a different name or remove it first."
        if "directory" in msg and "not empty" in msg:
            return "Directory is not empty. Remove contents first or use recursive delete."

        return f"Check the arguments passed to '{tool_name}' and try again."

    async def list_tools(self) -> list[dict]:
        """List available tools from the MCP server."""
        response = await self._send_request("tools/list", {})
        return response.get("result", {}).get("tools", [])

    async def disconnect(self) -> None:
        """Gracefully shut down the MCP server connection."""
        if self._process:
            try:
                self._process.stdin.close()
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                self._process.kill()
            finally:
                self._process = None
                self._initialized = False
