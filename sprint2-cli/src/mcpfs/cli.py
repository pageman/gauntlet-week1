"""mcpfs CLI — Command-line interface for MCP filesystem operations.

This module defines the CLI commands using Click and handles:
- Command routing and argument parsing
- Output formatting with Rich
- Error presentation (no raw stack traces)
- MCP client lifecycle management
"""

import asyncio
import os
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text

from .mcp_client import MCPClient, MCPError, MCPConnectionError, MCPToolError
from .operations import FileOperations


console = Console()
error_console = Console(stderr=True)


def get_mcp_client() -> MCPClient:
    """Create an MCP client configured for the filesystem server."""
    server_path = os.environ.get("MCP_SERVER_PATH", "/tmp/mcpfs-workspace")
    server_cmd = os.environ.get(
        "MCP_SERVER_CMD",
        "npx,-y,@modelcontextprotocol/server-filesystem," + server_path,
    ).split(",")

    return MCPClient(
        server_command=server_cmd,
        allowed_paths=[server_path],
    )


def run_async(coro):
    """Run an async function in the event loop."""
    try:
        return asyncio.run(coro)
    except KeyboardInterrupt:
        error_console.print("[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(130)


def handle_error(e: Exception) -> None:
    """Display error in user-friendly format with suggestions."""
    if isinstance(e, MCPConnectionError):
        error_console.print(Panel(
            f"[red bold]Connection Error[/red bold]\n\n{e.message}",
            title="Error",
            border_style="red",
        ))
        if e.suggestion:
            error_console.print(f"\n[yellow]Suggestion:[/yellow] {e.suggestion}")
        sys.exit(2)
    elif isinstance(e, MCPToolError):
        error_console.print(Panel(
            f"[red bold]Operation Failed[/red bold]\n\n{e.message}",
            title="Error",
            border_style="red",
        ))
        if e.suggestion:
            error_console.print(f"\n[yellow]Suggestion:[/yellow] {e.suggestion}")
        sys.exit(1)
    elif isinstance(e, MCPError):
        error_console.print(f"[red]Error:[/red] {e.message}")
        sys.exit(1)
    else:
        error_console.print(Panel(
            f"[red bold]Unexpected Error[/red bold]\n\n"
            f"An internal error occurred. This is likely a bug in mcpfs.\n"
            f"Error type: {type(e).__name__}",
            title="Internal Error",
            border_style="red",
        ))
        sys.exit(2)


@click.group()
@click.version_option(version="1.0.0", prog_name="mcpfs")
def cli():
    """mcpfs — Intelligent file operations via Model Context Protocol.

    A CLI tool that connects to an MCP filesystem server to provide
    search, analysis, and management of files through a structured
    protocol interface.
    """
    pass


@cli.command()
@click.argument("pattern")
@click.option("--path", "-p", default=".", help="Directory to search in")
def search(pattern: str, path: str):
    """Search for files matching a glob pattern.

    Examples:
        mcpfs search "*.py"
        mcpfs search "test_*" --path ./tests
        mcpfs search "*.md" --path /home/user/docs
    """
    async def _search():
        client = get_mcp_client()
        try:
            await client.connect()
            ops = FileOperations(client)
            results = await ops.search_files(pattern, path)

            if not results:
                console.print(f"[yellow]No files matching '{pattern}' found in {path}[/yellow]")
                return

            table = Table(title=f"Search Results: {pattern}")
            table.add_column("File", style="cyan")
            table.add_column("Path", style="dim")

            for filepath in results:
                name = os.path.basename(filepath)
                directory = os.path.dirname(filepath)
                table.add_row(name, directory)

            console.print(table)
            console.print(f"\n[green]{len(results)} file(s) found[/green]")
        finally:
            await client.disconnect()

    try:
        run_async(_search())
    except MCPError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("path", default=".")
@click.option("--depth", "-d", default=3, help="Maximum depth to display")
def tree(path: str, depth: int):
    """Display directory tree structure.

    Examples:
        mcpfs tree
        mcpfs tree ./src --depth 2
        mcpfs tree /home/user/project
    """
    async def _tree():
        client = get_mcp_client()
        try:
            await client.connect()
            ops = FileOperations(client)
            entries = await ops.list_directory(path)

            abs_path = os.path.abspath(path)
            tree_widget = Tree(f"[bold blue]{abs_path}[/bold blue]")

            dirs = sorted([e for e in entries if e.is_directory], key=lambda x: x.name)
            files = sorted([e for e in entries if not e.is_directory], key=lambda x: x.name)

            for d in dirs:
                tree_widget.add(f"[bold blue]{d.name}/[/bold blue]")

            for f in files:
                tree_widget.add(f"[green]{f.name}[/green]")

            console.print(tree_widget)
            console.print(f"\n[dim]{len(dirs)} directories, {len(files)} files[/dim]")
        finally:
            await client.disconnect()

    try:
        run_async(_tree())
    except MCPError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("file")
def info(file: str):
    """Get detailed information about a file.

    Examples:
        mcpfs info ./main.py
        mcpfs info /home/user/config.yaml
        mcpfs info README.md
    """
    async def _info():
        client = get_mcp_client()
        try:
            await client.connect()
            ops = FileOperations(client)
            file_info = await ops.get_file_info(file)

            table = Table(title=f"File Info: {file_info.name}", show_header=False)
            table.add_column("Property", style="bold")
            table.add_column("Value")

            table.add_row("Path", file_info.path)
            table.add_row("Type", file_info.file_type)
            table.add_row("Size", _format_size(file_info.size))
            table.add_row("Is Directory", "Yes" if file_info.is_directory else "No")
            if file_info.modified:
                table.add_row("Modified", file_info.modified)

            console.print(table)
        finally:
            await client.disconnect()

    try:
        run_async(_info())
    except MCPError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("file")
@click.option("--lines", "-n", default=None, type=int, help="Number of lines to show")
def read(file: str, lines: Optional[int]):
    """Read and display file contents.

    Examples:
        mcpfs read ./config.yaml
        mcpfs read main.py --lines 20
        mcpfs read /home/user/notes.txt -n 50
    """
    async def _read():
        client = get_mcp_client()
        try:
            await client.connect()
            ops = FileOperations(client)
            content = await ops.read_file(file, max_lines=lines)

            console.print(Panel(
                content,
                title=f"[bold]{file}[/bold]",
                border_style="blue",
            ))
        finally:
            await client.disconnect()

    try:
        run_async(_read())
    except MCPError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("file")
@click.option("--content", "-c", required=True, help="Content to write to the file")
def create(file: str, content: str):
    """Create a new file with specified content.

    Examples:
        mcpfs create ./note.txt --content "Remember to review PR"
        mcpfs create config.json -c '{"key": "value"}'
        mcpfs create README.md --content "# My Project"
    """
    async def _create():
        client = get_mcp_client()
        try:
            await client.connect()
            ops = FileOperations(client)
            result = await ops.create_file(file, content)
            console.print(f"[green]✓[/green] {result}")
        finally:
            await client.disconnect()

    try:
        run_async(_create())
    except MCPError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("source")
@click.argument("dest")
def move(source: str, dest: str):
    """Move or rename a file.

    Examples:
        mcpfs move ./old_name.txt ./new_name.txt
        mcpfs move ./src/temp.py ./src/utils.py
        mcpfs move draft.md final.md
    """
    async def _move():
        client = get_mcp_client()
        try:
            await client.connect()
            ops = FileOperations(client)
            result = await ops.move_file(source, dest)
            console.print(f"[green]✓[/green] {result}")
        finally:
            await client.disconnect()

    try:
        run_async(_move())
    except MCPError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


@cli.command()
@click.argument("path", default=".")
def stats(path: str):
    """Show directory statistics.

    Examples:
        mcpfs stats
        mcpfs stats ./src
        mcpfs stats /home/user/project
    """
    async def _stats():
        client = get_mcp_client()
        try:
            await client.connect()
            ops = FileOperations(client)
            dir_stats = await ops.get_directory_stats(path)

            table = Table(title=f"Directory Stats: {dir_stats['path']}")
            table.add_column("Metric", style="bold")
            table.add_column("Value", justify="right")

            table.add_row("Total Entries", str(dir_stats["total_entries"]))
            table.add_row("Directories", str(dir_stats["directories"]))
            table.add_row("Files", str(dir_stats["files"]))

            console.print(table)

            if dir_stats["file_types"]:
                type_table = Table(title="File Types")
                type_table.add_column("Extension", style="cyan")
                type_table.add_column("Count", justify="right")

                for ext, count in sorted(
                    dir_stats["file_types"].items(), key=lambda x: x[1], reverse=True
                ):
                    type_table.add_row(ext, str(count))

                console.print(type_table)
        finally:
            await client.disconnect()

    try:
        run_async(_stats())
    except MCPError as e:
        handle_error(e)
    except Exception as e:
        handle_error(e)


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
