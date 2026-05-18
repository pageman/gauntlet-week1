"""File operations module — wraps MCP tool calls with business logic.

Each function in this module corresponds to a CLI command and handles:
1. Argument preparation for the MCP tool call
2. Response parsing and formatting
3. Error translation to user-friendly messages
"""

import os
import re
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .mcp_client import MCPClient, MCPToolError


MAX_PREVIEW_BYTES = 100_000
MAX_PREVIEW_LINES = 1000
SAFE_GLOB_RE = re.compile(r"^[A-Za-z0-9*?\[\]_.-]+$")
audit_logger = logging.getLogger("mcpfs.audit")


@dataclass
class FileInfo:
    """Structured file information."""
    path: str
    name: str
    size: int
    is_directory: bool
    modified: str = ""
    line_count: int = 0
    file_type: str = "unknown"


@dataclass
class DirectoryEntry:
    """Entry in a directory listing."""
    name: str
    is_directory: bool
    path: str


class FileOperations:
    """High-level file operations using MCP protocol.

    This class provides the business logic layer between the CLI commands
    and the raw MCP protocol calls. It handles path resolution, response
    parsing, and error context enrichment.
    """

    def __init__(self, client: MCPClient):
        self.client = client

    def _parse_text_result(self, result: list[dict]) -> str:
        """Extract text content from an MCP tool result."""
        if not isinstance(result, list):
            raise MCPToolError(
                "MCP server returned a malformed response",
                suggestion="Verify the requested tool is supported by this MCP server.",
            )
        chunks: list[str] = []
        saw_text = False
        for item in result:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type")
            text = item.get("text", "")
            if item_type == "error":
                raise MCPToolError(
                    text or "MCP server returned an error result",
                    suggestion="Check the path, permissions, and MCP server output.",
                )
            if item_type == "text":
                saw_text = True
                chunks.append(text)
        if not saw_text:
            raise MCPToolError(
                "MCP server returned an empty or unsupported response",
                suggestion="Verify the requested tool is supported by this MCP server.",
            )
        return "".join(chunks)

    def _is_path_allowed(self, abs_path: str, allowed_roots: list[str]) -> bool:
        """Return true when a real path stays inside at least one allowed root."""
        try:
            real_path = os.path.normcase(os.path.realpath(abs_path))
            for root in allowed_roots:
                real_root = os.path.normcase(os.path.realpath(root))
                if os.path.commonpath([real_root, real_path]) == real_root:
                    return True
        except (OSError, ValueError):
            return False
        return False

    def _is_safe_entry_name(self, name: str) -> bool:
        """Reject directory-listing names that would escape the shown directory."""
        if not name or name in {".", ".."}:
            return False
        return "/" not in name and "\\" not in name

    def _resolve_path(self, path: str) -> str:
        """Resolve a path and ensure it remains within an allowed MCP root.

        The CLI may normalize paths for display and for client-side guardrails,
        but metadata, listing, reading, writing, and moving still happen through
        MCP tool calls.
        """
        abs_path = os.path.realpath(os.path.abspath(path))
        allowed_paths = [os.path.realpath(os.path.abspath(root)) for root in self.client.allowed_paths]
        if allowed_paths and not self._is_path_allowed(abs_path, allowed_paths):
            roots = ", ".join(allowed_paths)
            raise MCPToolError(
                f"Path '{path}' is outside the configured MCP workspace",
                suggestion=f"Use a path under one of the allowed roots: {roots}",
            )
        return abs_path

    async def search_files(self, pattern: str, search_path: str = ".") -> list[str]:
        """Search for files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "*.py", "test_*")
            search_path: Directory to search in

        Returns:
            List of matching file paths
        """
        if (
            ".." in pattern
            or "/" in pattern
            or "\\" in pattern
            or os.path.isabs(pattern)
            or not SAFE_GLOB_RE.fullmatch(pattern)
        ):
            raise MCPToolError(
                f"Unsafe search pattern: {pattern}",
                suggestion="Use a filename glob such as '*.py' or 'test_*' without path separators.",
            )

        abs_path = self._resolve_path(search_path)
        audit_logger.info("action=search_files path=%s pattern=%s", abs_path, pattern)

        try:
            result = await self.client.call_tool("search_files", {
                "path": abs_path,
                "pattern": pattern,
            })
        except MCPToolError as e:
            if "not found" in e.message.lower() or "no such" in e.message.lower():
                raise MCPToolError(
                    f"Search path '{search_path}' does not exist",
                    suggestion=f"Verify the directory exists: ls -la {search_path}",
                )
            raise

        matches = []
        text = self._parse_text_result(result)
        for line in text.strip().split("\n"):
            if line.strip():
                matches.append(line.strip())

        return matches

    async def list_directory(self, path: str = ".") -> list[DirectoryEntry]:
        """List contents of a directory.

        Args:
            path: Directory path to list

        Returns:
            List of directory entries
        """
        abs_path = self._resolve_path(path)
        audit_logger.info("action=list_directory path=%s", abs_path)

        try:
            result = await self.client.call_tool("list_directory", {
                "path": abs_path,
            })
        except MCPToolError as e:
            if "not found" in e.message.lower():
                raise MCPToolError(
                    f"Directory '{path}' does not exist",
                    suggestion="Use 'mcpfs tree' to see available directories.",
                )
            raise

        entries = []
        text = self._parse_text_result(result)
        for line in text.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("[DIR]"):
                name = line.replace("[DIR]", "").strip()
                is_directory = True
            elif line.startswith("[FILE]"):
                name = line.replace("[FILE]", "").strip()
                is_directory = False
            else:
                name = line
                is_directory = False
            if not self._is_safe_entry_name(name):
                continue
            entry_path = self._resolve_path(os.path.join(abs_path, name))
            entries.append(DirectoryEntry(
                name=name,
                is_directory=is_directory,
                path=entry_path,
            ))

        return entries

    async def get_file_info(self, path: str) -> FileInfo:
        """Get detailed information about a file.

        Args:
            path: Path to the file

        Returns:
            FileInfo with metadata
        """
        abs_path = self._resolve_path(path)
        audit_logger.info("action=get_file_info path=%s", abs_path)

        try:
            result = await self.client.call_tool("get_file_info", {
                "path": abs_path,
            })
        except MCPToolError as e:
            if "not found" in e.message.lower():
                raise MCPToolError(
                    f"File '{path}' does not exist",
                    suggestion=f"Check the path. Use 'mcpfs search \"{Path(path).name}\"' to find it.",
                )
            raise

        info_text = self._parse_text_result(result)

        # Extract metadata from response text
        size = 0
        is_dir = False
        modified = ""
        name = os.path.basename(abs_path)

        for line in info_text.split("\n"):
            line_lower = line.lower().strip()
            if "size:" in line_lower:
                try:
                    size = int("".join(c for c in line.split(":")[-1] if c.isdigit()))
                except ValueError:
                    pass
            if "directory" in line_lower and ("true" in line_lower or "yes" in line_lower):
                is_dir = True
            if "modified" in line_lower:
                modified = line.split(":", 1)[-1].strip() if ":" in line else ""

        # Determine file type from extension
        ext = Path(abs_path).suffix.lower()
        type_map = {
            ".py": "Python source",
            ".js": "JavaScript source",
            ".ts": "TypeScript source",
            ".json": "JSON data",
            ".yaml": "YAML config",
            ".yml": "YAML config",
            ".md": "Markdown document",
            ".txt": "Plain text",
            ".html": "HTML document",
            ".css": "CSS stylesheet",
            ".toml": "TOML config",
            ".cfg": "Configuration",
            ".ini": "INI config",
        }
        file_type = type_map.get(ext, f"{ext} file" if ext else "unknown")

        return FileInfo(
            path=abs_path,
            name=name,
            size=size,
            is_directory=is_dir,
            modified=modified,
            file_type=file_type,
        )

    async def read_file(self, path: str, max_lines: Optional[int] = None) -> str:
        """Read file contents.

        Args:
            path: Path to the file
            max_lines: If set, only return this many lines

        Returns:
            File content as string
        """
        abs_path = self._resolve_path(path)
        audit_logger.info("action=read_file path=%s max_lines=%s", abs_path, max_lines)

        try:
            result = await self.client.call_tool("read_file", {
                "path": abs_path,
            })
        except MCPToolError as e:
            if "not found" in e.message.lower():
                raise MCPToolError(
                    f"File '{path}' does not exist",
                    suggestion=f"Check the path. Use 'mcpfs search' to find files.",
                )
            if "permission" in e.message.lower():
                raise MCPToolError(
                    f"Permission denied reading '{path}'",
                    suggestion=f"Check file permissions: ls -la {path}",
                )
            if "directory" in e.message.lower():
                raise MCPToolError(
                    f"'{path}' is a directory, not a file",
                    suggestion="Use 'mcpfs tree' to list directory contents.",
                )
            raise

        content = self._parse_text_result(result)

        encoded = content.encode("utf-8", errors="replace")
        if len(encoded) > MAX_PREVIEW_BYTES:
            content = encoded[:MAX_PREVIEW_BYTES].decode("utf-8", errors="replace")
            content += f"\n... (truncated after {MAX_PREVIEW_BYTES} bytes)"

        if max_lines is not None:
            lines = content.split("\n")
            content = "\n".join(lines[:max_lines])
            if len(lines) > max_lines:
                content += f"\n... ({len(lines) - max_lines} more lines)"
        else:
            lines = content.split("\n")
            if len(lines) > MAX_PREVIEW_LINES:
                content = "\n".join(lines[:MAX_PREVIEW_LINES])
                content += f"\n... ({len(lines) - MAX_PREVIEW_LINES} more lines)"

        return content

    async def create_file(self, path: str, content: str) -> str:
        """Create a new file with content.

        Args:
            path: Path for the new file
            content: File content

        Returns:
            Confirmation message
        """
        try:
            content.encode("utf-8").decode("utf-8")
        except UnicodeError as exc:
            raise MCPToolError(
                "File content must be valid UTF-8 text",
                suggestion="Write binary files outside mcpfs or encode them as text first.",
            ) from exc

        abs_path = self._resolve_path(path)
        audit_logger.info("action=create_file path=%s bytes=%s", abs_path, len(content.encode("utf-8")))

        try:
            await self.client.call_tool("write_file", {
                "path": abs_path,
                "content": content,
            })
        except MCPToolError as e:
            if "permission" in e.message.lower():
                raise MCPToolError(
                    f"Permission denied creating '{path}'",
                    suggestion=f"Check directory permissions: ls -la {os.path.dirname(abs_path)}",
                )
            raise

        return f"Created: {abs_path}"

    async def move_file(self, source: str, destination: str) -> str:
        """Move or rename a file.

        Args:
            source: Current file path
            destination: New file path

        Returns:
            Confirmation message
        """
        abs_source = self._resolve_path(source)
        abs_dest = self._resolve_path(destination)
        audit_logger.info("action=move_file source=%s destination=%s", abs_source, abs_dest)

        try:
            await self.client.call_tool("move_file", {
                "source": abs_source,
                "destination": abs_dest,
            })
        except MCPToolError as e:
            if "not found" in e.message.lower():
                raise MCPToolError(
                    f"Source file '{source}' does not exist",
                    suggestion="Verify the source path. Use 'mcpfs search' to find files.",
                )
            if "already exists" in e.message.lower():
                raise MCPToolError(
                    f"Destination '{destination}' already exists",
                    suggestion="Choose a different destination or remove the existing file.",
                )
            raise

        return f"Moved: {abs_source} → {abs_dest}"

    async def get_directory_stats(self, path: str = ".") -> dict:
        """Get statistics about a directory.

        Args:
            path: Directory to analyze

        Returns:
            Dictionary with file counts, sizes, and type breakdown
        """
        abs_path = self._resolve_path(path)
        audit_logger.info("action=get_directory_stats path=%s", abs_path)
        entries = await self.list_directory(path)

        stats = {
            "path": abs_path,
            "total_entries": len(entries),
            "directories": sum(1 for e in entries if e.is_directory),
            "files": sum(1 for e in entries if not e.is_directory),
            "file_types": {},
        }

        for entry in entries:
            if not entry.is_directory:
                ext = Path(entry.name).suffix.lower() or "(no extension)"
                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

        return stats
