# mcpfs — Intelligent File Operations via Model Context Protocol

A command-line tool that integrates with the Model Context Protocol (MCP) filesystem server to provide intelligent file operations without raw stack traces or direct filesystem access.

## Quick Start

### Installation

```bash
# Clone and install
git clone <repo-url>
cd sprint2-cli

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .
```

### Configuration

Set environment variables to configure the MCP server:

```bash
# Default: uses npx to run @modelcontextprotocol/server-filesystem
export MCP_SERVER_PATH="/path/to/workspace"
export MCP_SERVER_CMD="npx,-y,@modelcontextprotocol/server-filesystem,/path/to/workspace"
```

### Usage

```bash
# Search for files
mcpfs search "*.py" --path ./src

# Show directory tree
mcpfs tree ./project --depth 3

# Get file information
mcpfs info ./main.py

# Read file contents
mcpfs read ./config.yaml --lines 20

# Create a new file
mcpfs create ./note.txt --content "Hello, World!"

# Move/rename a file
mcpfs move ./old.txt ./new.txt

# Get directory statistics
mcpfs stats ./src
```

## Commands

### search

Search for files matching a glob pattern.

```bash
mcpfs search <pattern> [--path DIR]
```

**Example:**
```bash
mcpfs search "test_*.py" --path ./tests
```

### tree

Display directory structure with optional depth limit.

```bash
mcpfs tree [path] [--depth N]
```

**Example:**
```bash
mcpfs tree ./project --depth 2
```

### info

Get detailed metadata about a file.

```bash
mcpfs info <file>
```

**Example:**
```bash
mcpfs info ./app.py
```

### read

Read and display file contents.

```bash
mcpfs read <file> [--lines N]
```

**Example:**
```bash
mcpfs read ./README.md --lines 50
```

### create

Create a new file with specified content.

```bash
mcpfs create <file> --content TEXT
```

**Example:**
```bash
mcpfs create ./config.json --content '{"debug": true}'
```

### move

Move or rename a file.

```bash
mcpfs move <source> <destination>
```

**Example:**
```bash
mcpfs move ./old_name.py ./new_name.py
```

### stats

Show directory statistics (file counts, types).

```bash
mcpfs stats [path]
```

**Example:**
```bash
mcpfs stats ./src
```

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

### Layers

1. **CLI Layer** (`cli.py`) — Command routing, argument parsing, output formatting
2. **Operations Layer** (`operations.py`) — Business logic, error translation, path resolution
3. **Protocol Layer** (`mcp_client.py`) — JSON-RPC 2.0 over stdio, connection management

## Error Handling

All errors are presented as actionable messages with suggestions:

```
╭─ Error ─────────────────────────────────────────╮
│ Connection Error                                │
│                                                 │
│ Cannot connect to MCP server. Ensure the       │
│ server is running: npx @modelcontextprotocol/  │
│ server-filesystem /path                        │
╰─────────────────────────────────────────────────╯

Suggestion: Check that the server binary has execute permissions.
```

No raw stack traces are ever shown to users.

## Exit Codes

- `0` — Success
- `1` — User error (invalid input, file not found, etc.)
- `2` — System error (connection failure, permission denied, etc.)
- `130` — Operation cancelled by user (Ctrl+C)

## Testing

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=mcpfs
```

## Known Limitations

1. **Requires running MCP server** — Must have Node.js and @modelcontextprotocol/server-filesystem installed
2. **No recursive tree** — Tree command shows only one level deep (use --depth to control)
3. **No content grep** — Search is pattern-based, not content-based
4. **No persistent connection** — Each command creates a new connection to the server
5. **Binary file issues** — Large or binary files may not display correctly
6. **No wildcard operations** — Move/create don't support wildcards
7. **Node.js dependency** — Requires Node.js for the MCP server

## Development

### Adding a New Command

1. Add the command function in `cli.py` with `@cli.command()` decorator
2. Implement the business logic in `operations.py`
3. Add error handling with actionable messages
4. Update this README with usage examples
5. Add tests in `tests/`

### Code Structure

```
src/mcpfs/
├── __init__.py          # Package initialization
├── cli.py               # CLI commands and output formatting
├── operations.py        # Business logic and error translation
└── mcp_client.py        # MCP protocol implementation

tests/
├── __init__.py
├── conftest.py          # Pytest fixtures
├── test_cli.py          # CLI tests
└── test_operations.py   # Operations tests
```

## Support

For issues or questions:
- Check the error message suggestions
- Review the SPEC.md for detailed requirements
- Examine test files for usage examples
- Check MCP server logs for protocol errors

## AI Interaction Log

This project was built using AI-first methodology with strict validation discipline. All AI-generated code was:

1. **Reviewed** — Every function read and understood before committing
2. **Tested** — Comprehensive test suite validates all behavior
3. **Validated** — Security and error handling verified
4. **Owned** — All changes documented and explained

See `AI-INTERACTION-LOG.md` for detailed session logs.
