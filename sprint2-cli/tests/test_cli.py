import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_parse_server_command_accepts_json_array():
    from mcpfs.cli import _parse_server_command

    command = _parse_server_command('["python","server.py","/tmp/workspace"]', "/tmp/workspace")

    assert command == ["python", "server.py", "/tmp/workspace"]


def test_parse_server_command_accepts_shell_words():
    from mcpfs.cli import _parse_server_command

    command = _parse_server_command('python "fake server.py" /tmp/workspace', "/tmp/workspace")

    assert command == ["python", "fake server.py", "/tmp/workspace"]


def test_parse_server_command_accepts_legacy_comma_form():
    from mcpfs.cli import _parse_server_command

    command = _parse_server_command("python,server.py,/tmp/workspace", "/tmp/workspace")

    assert command == ["python", "server.py", "/tmp/workspace"]


def run_cli(cli_env, *args):
    return subprocess.run(
        [sys.executable, "-m", "mcpfs.cli", *args],
        cwd=cli_env["MCP_SERVER_PATH"],
        env=cli_env,
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_cli_help(cli_env):
    result = run_cli(cli_env, "--help")

    assert result.returncode == 0
    assert "mcpfs" in result.stdout
    assert "search" in result.stdout


def test_cli_search_uses_mcp_server(cli_env):
    result = run_cli(cli_env, "search", "*.md", "--path", ".")

    assert result.returncode == 0, result.stderr
    assert "README.md" in result.stdout
    assert "deep.md" in result.stdout


def test_cli_tree_honors_depth(cli_env):
    result = run_cli(cli_env, "tree", ".", "--depth", "2")

    assert result.returncode == 0, result.stderr
    assert "src/" in result.stdout
    assert "app.py" in result.stdout
    assert "Displayed to depth 2" in result.stdout


def test_cli_info(cli_env):
    result = run_cli(cli_env, "info", "README.md")

    assert result.returncode == 0, result.stderr
    assert "README.md" in result.stdout
    assert "Markdown document" in result.stdout


def test_cli_read_limits_lines(cli_env):
    result = run_cli(cli_env, "read", "README.md", "--lines", "3")

    assert result.returncode == 0, result.stderr
    assert "# Demo" in result.stdout
    assert "hello" in result.stdout
    assert "world" not in result.stdout


def test_cli_rejects_negative_line_limit(cli_env):
    result = run_cli(cli_env, "read", "README.md", "--lines", "-1")

    assert result.returncode != 0
    assert "Invalid value" in result.stderr


def test_cli_create_file(cli_env, workspace):
    result = run_cli(cli_env, "create", "created.txt", "--content", "created through mcp")

    assert result.returncode == 0, result.stderr
    assert "Created:" in result.stdout
    assert (workspace / "created.txt").read_text(encoding="utf-8") == "created through mcp"


def test_cli_move_file(cli_env, workspace):
    source = workspace / "move-me.txt"
    source.write_text("move me", encoding="utf-8")

    result = run_cli(cli_env, "move", "move-me.txt", "moved.txt")

    assert result.returncode == 0, result.stderr
    assert "Moved:" in result.stdout
    assert not source.exists()
    assert (workspace / "moved.txt").exists()


def test_cli_stats(cli_env):
    result = run_cli(cli_env, "stats", ".")

    assert result.returncode == 0, result.stderr
    assert "Directory Stats" in result.stdout
    assert "Total Entries" in result.stdout


def test_cli_missing_file_error_is_actionable(cli_env):
    result = run_cli(cli_env, "read", "missing-file.md")

    assert result.returncode != 0
    assert "Operation Failed" in result.stderr
    assert "does not exist" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_rejects_path_outside_workspace(cli_env, tmp_path):
    outside = tmp_path.parent / "outside-workspace.txt"
    outside.write_text("outside", encoding="utf-8")

    result = run_cli(cli_env, "read", str(outside))

    assert result.returncode != 0
    assert "outside the configured MCP workspace" in result.stderr
    assert "Traceback" not in result.stderr
