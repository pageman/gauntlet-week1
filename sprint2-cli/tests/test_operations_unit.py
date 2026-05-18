import builtins
import os
from pathlib import Path

import pytest

from mcpfs.mcp_client import MCPToolError
from mcpfs.operations import FileOperations


class FakeClient:
    def __init__(self, root):
        self.allowed_paths = [str(root)]
        self.calls = []

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "search_files":
            return [{"type": "text", "text": "/workspace/a.md\n/workspace/b.md"}]
        if name == "list_directory":
            return [{"type": "text", "text": "[DIR] src\n[FILE] README.md"}]
        if name == "get_file_info":
            return [{"type": "text", "text": "Size: 12\nDirectory: false\nModified: today"}]
        if name == "read_file":
            return [{"type": "text", "text": "one\ntwo\nthree\n"}]
        if name in {"write_file", "move_file"}:
            return [{"type": "text", "text": "ok"}]
        raise AssertionError(f"unexpected tool: {name}")


@pytest.mark.asyncio
async def test_search_files_parses_newline_results(workspace):
    ops = FileOperations(FakeClient(workspace))
    results = await ops.search_files("*.md", str(workspace))

    assert results == ["/workspace/a.md", "/workspace/b.md"]


@pytest.mark.asyncio
async def test_list_directory_parses_file_and_directory_entries(workspace):
    ops = FileOperations(FakeClient(workspace))
    entries = await ops.list_directory(str(workspace))

    assert [(entry.name, entry.is_directory) for entry in entries] == [
        ("src", True),
        ("README.md", False),
    ]


@pytest.mark.asyncio
async def test_get_file_info_maps_basic_metadata(workspace):
    ops = FileOperations(FakeClient(workspace))
    info = await ops.get_file_info(str(workspace / "README.md"))

    assert info.name == "README.md"
    assert info.size == 12
    assert info.file_type == "Markdown document"


@pytest.mark.asyncio
async def test_read_file_truncates_lines(workspace):
    ops = FileOperations(FakeClient(workspace))
    content = await ops.read_file(str(workspace / "README.md"), max_lines=2)

    assert content.startswith("one\ntwo")
    assert "more lines" in content


@pytest.mark.asyncio
async def test_create_file_uses_mcp_not_direct_write(monkeypatch, workspace):
    def fail_open(*args, **kwargs):
        raise AssertionError("direct file open is forbidden")

    monkeypatch.setattr(builtins, "open", fail_open)
    monkeypatch.setattr(Path, "write_text", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("direct write_text is forbidden")))

    fake = FakeClient(workspace)
    ops = FileOperations(fake)
    result = await ops.create_file(str(workspace / "new.txt"), "hello")

    assert result.startswith("Created:")
    assert fake.calls[-1][0] == "write_file"


@pytest.mark.asyncio
async def test_move_file_uses_mcp_not_direct_move(monkeypatch, workspace):
    import shutil

    monkeypatch.setattr(shutil, "move", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("direct move is forbidden")))

    fake = FakeClient(workspace)
    ops = FileOperations(fake)
    result = await ops.move_file(str(workspace / "old.txt"), str(workspace / "new.txt"))

    assert result.startswith("Moved:")
    assert fake.calls[-1][0] == "move_file"


@pytest.mark.asyncio
async def test_directory_stats_counts_entries(workspace):
    ops = FileOperations(FakeClient(workspace))
    stats = await ops.get_directory_stats(str(workspace))

    assert stats["total_entries"] == 2
    assert stats["directories"] == 1
    assert stats["files"] == 1
    assert stats["file_types"][".md"] == 1


@pytest.mark.asyncio
async def test_rejects_paths_outside_allowed_root(workspace, tmp_path):
    ops = FileOperations(FakeClient(workspace))

    with pytest.raises(MCPToolError) as exc_info:
        await ops.read_file(str(tmp_path.parent / "outside.txt"))

    assert "outside the configured MCP workspace" in exc_info.value.message
