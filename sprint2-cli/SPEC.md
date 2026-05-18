# Sprint 2 Specification: MCP-Integrated CLI Tool — `mcpfs`

## Overview

`mcpfs` is a command-line tool that integrates with the Model Context Protocol (MCP) filesystem server to provide intelligent file operations. It allows users to search, analyze, and manage files through a structured protocol interface rather than direct filesystem calls.

## What It Does

A CLI tool that connects to an MCP filesystem server and provides:

1. **File search** — Find files by name pattern, content, or metadata
2. **File analysis** — Get summaries of file contents (size, type, line count, structure)
3. **Directory tree** — Display directory structure with filtering
4. **File operations** — Read, create, and move files via MCP protocol
5. **Batch operations** — Apply operations to multiple files matching a pattern

## MCP Integration

The tool communicates with an MCP server using the Model Context Protocol:

- Connects via stdio transport to a local MCP filesystem server
- Uses JSON-RPC 2.0 over stdio. The default transport is newline-delimited
  JSON for compatibility with the official JavaScript filesystem server; an
  explicit `content-length` mode is also supported for header-framed servers.
- Calls MCP tools: `read_file`, `write_file`, `list_directory`, `search_files`, `get_file_info`, `move_file`
- Handles MCP protocol errors gracefully

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `mcpfs search <pattern> [--path DIR]` | Search for files matching pattern | `mcpfs search "*.py" --path ./src` |
| `mcpfs tree [path] [--depth N]` | Show directory tree | `mcpfs tree ./project --depth 3` |
| `mcpfs info <file>` | Get file metadata and summary | `mcpfs info ./main.py` |
| `mcpfs read <file> [--lines N]` | Read file contents | `mcpfs read ./config.yaml --lines 20` |
| `mcpfs create <file> --content TEXT` | Create a new file | `mcpfs create ./note.txt --content "Hello"` |
| `mcpfs move <source> <dest>` | Move/rename a file | `mcpfs move ./old.txt ./new.txt` |
| `mcpfs stats [path]` | Show directory statistics | `mcpfs stats ./src` |

## Error Handling Strategy

All errors surface as actionable messages:

- **Connection errors**: "Cannot connect to MCP server. Ensure the server is running: `npx @modelcontextprotocol/server-filesystem /path`"
- **Permission errors**: "Permission denied for '{path}'. Check file permissions with `ls -la {path}`"
- **Not found**: "File '{path}' does not exist. Did you mean '{suggestion}'?"
- **Protocol errors**: "MCP server returned an unexpected response. Server may be incompatible (expected protocol version 2024-11-05)"

No raw stack traces are ever shown to the user. Internal errors are caught and translated to human-readable messages with suggested next steps.

## Architecture

```
┌─────────────┐     stdio      ┌──────────────────┐
│   mcpfs     │ ──────────────▶│  MCP Filesystem  │
│   (CLI)     │ ◀──────────────│     Server       │
└─────────────┘   JSON-RPC     └──────────────────┘
      │
      ▼
┌─────────────┐
│  User TTY   │
│  (output)   │
└─────────────┘
```

## Non-Functional Requirements

- Startup time target: < 500ms after the MCP server is warm
- Output: Formatted for terminal (colors, tables where appropriate)
- Exit codes: 0 for success, 1 for user errors, 2 for system errors
- No external API keys required
- Works offline (MCP server is local)

## Dependencies

- Python 3.11+
- Direct stdio transport implementation for MCP JSONL and Content-Length
  framing modes
- `click` for CLI framework
- `rich` for terminal formatting

## Success Criteria

1. All 7 commands work correctly with the MCP filesystem server
2. Error messages are always actionable (no stack traces)
3. README documents installation, usage, and limitations
4. Code handles MCP server being unavailable gracefully
5. File reads, writes, moves, metadata, and directory listing go through MCP tool
   calls. Client-side path normalization is allowed only for display and
   workspace-boundary checks.

## Implementation Notes

### Protocol Layer (mcp_client.py)

- Manages subprocess lifecycle for MCP server
- Implements JSON-RPC 2.0 message exchange
- Handles timeouts and connection errors
- Provides `connect()`, `call_tool()`, `disconnect()` interface

### Operations Layer (operations.py)

- Wraps raw MCP tool calls with business logic
- Translates MCP errors to user-friendly messages
- Handles path resolution and normalization
- Provides `search_files()`, `list_directory()`, `read_file()`, etc.

### CLI Layer (cli.py)

- Uses Click for command routing
- Uses Rich for terminal formatting
- Manages MCP client lifecycle (connect/disconnect)
- Handles errors and formats output

## Testing Strategy

- Unit tests for operations layer with a mocked MCP client
- Protocol tests using fake JSONL and Content-Length framed MCP servers
- CLI command tests against the fake MCP server
- Error handling tests for server-missing, path-missing, and workspace-boundary cases
- Edge case tests for empty directories, line limits, and path traversal attempts

## Deployment

- Installable via `pip install -e .` from source
- Can be packaged as standalone executable with PyInstaller
- Requires Node.js and @modelcontextprotocol/server-filesystem for official
  runtime verification

## Known Limitations

1. Requires running MCP server
2. Recursive tree is intentionally bounded by --depth
3. No content grep (pattern-based search only)
4. No persistent connection (new connection per command)
5. Binary file handling limited
6. No wildcard operations
7. Node.js dependency for server
