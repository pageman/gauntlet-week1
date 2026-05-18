"""File operations module — wraps MCP tool calls with business logic.

Each function in this module corresponds to a CLI command and handles:
1. Argument preparation for the MCP tool call
2. Response parsing and formatting
3. Error translation to user-friendly messages
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .mcp_client import MCPClient, MCPToolError, MCPConnectionError


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

    async def search_files(self, pattern: str, search_path: str = ".") -> list[str]:
        """Search for files matching a glob pattern.

        Args:
            pattern: Glob pattern (e.g., "*.py", "test_*")
            search_path: Directory to search in

        Returns:
            List of matching file paths
        """
        abs_path = os.path.abspath(search_path)

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

        # Parse results
        matches = []
        for item in result:
            if item.get("type") == "text":
                text = item.get("text", "")
                # Results come as newline-separated paths
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
        abs_path = os.path.abspath(path)

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
        for item in result:
            if item.get("type") == "text":
                text = item.get("text", "")
                for line in text.strip().split("\n"):
                    line = line.strip()
                    if not line:
                        continue
                    # Parse directory listing format
                    if line.startswith("[DIR]"):
                        name = line.replace("[DIR]", "").strip()
                        entries.append(DirectoryEntry(
                            name=name,
                            is_directory=True,
                            path=os.path.join(abs_path, name),
                        ))
                    elif line.startswith("[FILE]"):
                        name = line.replace("[FILE]", "").strip()
                        entries.append(DirectoryEntry(
                            name=name,
                            is_directory=False,
                            path=os.path.join(abs_path, name),
                        ))
                    else:
                        # Fallback: treat as file
                        entries.append(DirectoryEntry(
                            name=line,
                            is_directory=False,
                            path=os.path.join(abs_path, line),
                        ))

        return entries

    async def get_file_info(self, path: str) -> FileInfo:
        """Get detailed information about a file.

        Args:
            path: Path to the file

        Returns:
            FileInfo with metadata
        """
        abs_path = os.path.abspath(path)

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

        # Parse file info from response
        info_text = ""
        for item in result:
            if item.get("type") == "text":
                info_text += item.get("text", "")

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
        abs_path = os.path.abspath(path)

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

        content = ""
        for item in result:
            if item.get("type") == "text":
                content += item.get("text", "")

        if max_lines is not None:
            lines = content.split("\n")
            content = "\n".join(lines[:max_lines])
            if len(lines) > max_lines:
                content += f"\n... ({len(lines) - max_lines} more lines)"

        return content

    async def create_file(self, path: str, content: str) -> str:
        """Create a new file with content.

        Args:
            path: Path for the new file
            content: File content

        Returns:
            Confirmation message
        """
        abs_path = os.path.abspath(path)

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
        abs_source = os.path.abspath(source)
        abs_dest = os.path.abspath(destination)

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
        abs_path = os.path.abspath(path)
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
