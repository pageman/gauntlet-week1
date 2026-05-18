import os
import sys
from pathlib import Path

import pytest


SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_ROOT))


@pytest.fixture
def workspace(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n\nhello\nworld\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("alpha\nbeta\ngamma\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (tmp_path / "src" / "nested").mkdir()
    (tmp_path / "src" / "nested" / "deep.md").write_text("deep\n", encoding="utf-8")
    return tmp_path


@pytest.fixture
def fake_server_command():
    server = Path(__file__).with_name("fake_mcp_server.py")
    return [sys.executable, str(server)]


@pytest.fixture
def fake_content_length_server_command():
    server = Path(__file__).with_name("fake_mcp_server.py")
    return [sys.executable, str(server), "--content-length"]


@pytest.fixture
def fake_roots_server_command():
    server = Path(__file__).with_name("fake_mcp_server.py")
    return [sys.executable, str(server), "--request-roots"]


@pytest.fixture
def cli_env(workspace, fake_server_command):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SRC_ROOT)
    env["MCP_SERVER_PATH"] = str(workspace)
    env["MCP_SERVER_CMD"] = ",".join(fake_server_command)
    return env
