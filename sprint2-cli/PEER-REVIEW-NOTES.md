# Sprint 2 Adversarial Peer-Review Notes

Review type: adversarial AI-assisted review
Date: 2026-05-18
Scope: `sprint2-cli/`
Status: addressed in this repair pass, except where explicitly marked as
human-follow-up.

This is not a substitute for a human peer review if an instructor requires one.
It is included so reviewers can see the concrete comments and responses that
shaped the repair.

| # | Reviewer comment | Response | Patch / evidence | Status |
| ---: | --- | --- | --- | --- |
| 1 | The test folder is effectively empty, so Sprint 2 cannot claim review readiness. | Added protocol, operations, CLI, error, and boundary tests. | `tests/test_mcp_client.py`, `tests/test_operations_unit.py`, `tests/test_cli.py` | Addressed |
| 2 | The MCP client framing boundary was ambiguous and would fail if a server expected a different stdio framing mode. | Added explicit JSONL and `Content-Length` framing modes. JSONL is the default for the official JS filesystem server; `content-length` is tested for header-framed servers. | `src/mcpfs/mcp_client.py`, `tests/test_mcp_client.py` | Addressed |
| 3 | CLI behavior depends on an external MCP server, making tests brittle. | Added a deterministic fake MCP server that can speak both supported framing modes. | `tests/fake_mcp_server.py` | Addressed |
| 4 | Official MCP servers can ask the client for workspace roots before returning a tool result. | Added `roots/list` handling and a fake-server regression test. | `src/mcpfs/mcp_client.py`, `tests/test_mcp_client.py` | Addressed |
| 5 | The CLI may access paths outside the intended workspace if the server allows it. | Added client-side workspace root enforcement before tool calls. | `FileOperations._resolve_path()` | Addressed |
| 6 | `tree --depth` is documented, but the original implementation only showed one level. | Implemented recursive tree traversal to the requested depth. | `src/mcpfs/cli.py` | Addressed |
| 7 | The README references tests that do not exist. | Added the missing tests and updated the docs to match the implementation. | `README.md`, `tests/` | Addressed |
| 8 | The Sprint 2 AI log is missing. | Added a session-level ownership log with accepted/rejected/changed/tested entries. | `AI-INTERACTION-LOG.md` | Addressed |
| 9 | A real human reviewer still needs to review the CLI. | Kept this limitation explicit. | `EVIDENCE-MANIFEST.md`, `WEEK1-REPORT.md` | Human follow-up |

## Verification Commands

```bash
cd sprint2-cli
python -m pip install -e ".[dev]"
python -m pytest tests -q
```

## Human Follow-Up Needed

Ask a human reviewer to leave at least five comments on a pull request. Copy
those comments and responses below this section with links to the relevant
commits.
