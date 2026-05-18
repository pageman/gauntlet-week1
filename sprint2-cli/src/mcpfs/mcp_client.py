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
import os
import sys
from dataclasses import dataclass, field
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

        line = json.dumps(message) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()

        # Read response
        try:
            response_line = await asyncio.wait_for(
                self._process.stdout.readline(), timeout=10.0
            )
        except asyncio.TimeoutError:
            raise MCPConnectionError(
                "MCP server did not respond within 10 seconds",
                suggestion="The server may be unresponsive. Try restarting it.",
            )

        if not response_line:
            raise MCPConnectionError(
                "MCP server closed connection unexpectedly",
                suggestion="Check server logs for errors. The server process may have crashed.",
            )

        try:
            response = json.loads(response_line.decode())
        except json.JSONDecodeError:
            raise MCPConnectionError(
                "MCP server returned invalid JSON",
                suggestion="Server may be sending non-protocol output. Check stderr.",
            )

        return response

    async def _send_notification(self, method: str, params: dict) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        if self._process is None or self._process.stdin is None:
            return

        message = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        line = json.dumps(message) + "\n"
        self._process.stdin.write(line.encode())
        await self._process.stdin.drain()

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
