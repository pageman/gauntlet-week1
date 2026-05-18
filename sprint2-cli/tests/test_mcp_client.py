import pytest

from mcpfs.mcp_client import MCPClient, MCPConnectionError, MCPToolError


@pytest.mark.asyncio
async def test_connects_with_jsonl_framing_by_default(fake_server_command, workspace):
    client = MCPClient(server_command=fake_server_command, allowed_paths=[str(workspace)])
    try:
        await client.connect()
        tools = await client.list_tools()
    finally:
        await client.disconnect()

    assert {tool["name"] for tool in tools} >= {"read_file", "list_directory", "search_files"}


@pytest.mark.asyncio
async def test_connects_with_content_length_framing(fake_content_length_server_command, workspace):
    client = MCPClient(
        server_command=fake_content_length_server_command,
        allowed_paths=[str(workspace)],
        framing="content-length",
    )
    try:
        await client.connect()
        tools = await client.list_tools()
    finally:
        await client.disconnect()

    assert {tool["name"] for tool in tools} >= {"read_file", "list_directory", "search_files"}


@pytest.mark.asyncio
async def test_calls_read_file_tool(fake_server_command, workspace):
    client = MCPClient(server_command=fake_server_command, allowed_paths=[str(workspace)])
    try:
        await client.connect()
        result = await client.call_tool("read_file", {"path": str(workspace / "README.md")})
    finally:
        await client.disconnect()

    assert result[0]["type"] == "text"
    assert "hello" in result[0]["text"]


@pytest.mark.asyncio
async def test_answers_server_roots_list_request(fake_roots_server_command, workspace):
    client = MCPClient(server_command=fake_roots_server_command, allowed_paths=[str(workspace)])
    try:
        await client.connect()
        result = await client.call_tool("read_file", {"path": str(workspace / "README.md")})
    finally:
        await client.disconnect()

    assert result[0]["type"] == "text"
    assert "hello" in result[0]["text"]


@pytest.mark.asyncio
async def test_tool_errors_are_translated(fake_server_command, workspace):
    client = MCPClient(server_command=fake_server_command, allowed_paths=[str(workspace)])
    try:
        await client.connect()
        with pytest.raises(MCPToolError) as exc_info:
            await client.call_tool("read_file", {"path": str(workspace / "missing.md")})
    finally:
        await client.disconnect()

    assert "read_file" in exc_info.value.message
    assert exc_info.value.suggestion


@pytest.mark.asyncio
async def test_missing_server_command_is_actionable(workspace):
    client = MCPClient(server_command=["definitely-missing-mcp-server"], allowed_paths=[str(workspace)])

    with pytest.raises(MCPConnectionError) as exc_info:
        await client.connect()

    assert "Cannot find MCP server command" in exc_info.value.message
    assert "Ensure the MCP server is installed" in exc_info.value.suggestion
