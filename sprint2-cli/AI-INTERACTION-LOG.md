# Sprint 2 AI Interaction Log

Status: repaired after adversarial review.

This log records the AI-assisted work that moved Sprint 2 from "package-shaped
but untested" to a reviewable MCP CLI artifact. It is not a perfect raw export
of every token exchanged, but it captures the required ownership trail:
prompt/context, AI output summary, accepted changes, rejected changes, manual
edits, and verification.

## Session 1 - Red-Team Finding: Empty Sprint 2 Tests

Prompt/context:

```text
Adversarial review found sprint2-cli/tests contained only __init__.py while the
README and SPEC claimed a CLI/operations test strategy.
```

AI output summary:

- Add a fake MCP filesystem server for deterministic tests.
- Add tests for protocol framing, CLI commands, operation parsing, error paths,
  and workspace-boundary checks.

Accepted:

- `tests/fake_mcp_server.py`
- `tests/test_mcp_client.py`
- `tests/test_operations_unit.py`
- `tests/test_cli.py`

Rejected:

- Tests that require global Node.js or a network install of the official MCP
  filesystem server during every test run. Those belong in optional integration
  checks, not the default suite.

Manual changes:

- Kept the fake server intentionally small and standard-library only.
- Made the tests exercise MCP stdio framing directly rather than mocking the
  transport away.

Verification:

```bash
cd sprint2-cli
python -m pytest tests -q
```

Expected result after repair:

```text
24 passed
```

## Session 2 - Red-Team Finding: Incorrect MCP Stdio Framing Boundary

Prompt/context:

```text
The red-team review flagged stdio framing as a risk. The first repair used only
Content-Length framing, but an integration check against the current official
JavaScript filesystem server showed that server expects newline-delimited JSON.
The correct repair is therefore explicit framing support, not a single hidden
assumption.
```

AI output summary:

- Keep newline-delimited JSON as the default for the official JS filesystem
  server.
- Add an explicit `content-length` mode for header-framed servers.
- Read response headers until a blank line in `content-length` mode, then read
  exactly the declared body length.
- Keep the same public `MCPClient` interface.

Accepted:

- `_write_message()` with JSONL and `Content-Length` branches
- `_read_message()` dispatching to framing-specific readers
- `_send_request()` calling the framed transport
- `_send_notification()` using the same framed transport

Rejected:

- Bringing in a full MCP SDK just to hide the transport. The Week 1 defense
  requirement is better served by showing the protocol mechanics directly.

Manual changes:

- Added explicit, actionable errors for malformed headers, missing
  `Content-Length`, truncated bodies, and invalid JSON.
- Added `MCP_STDIO_FRAMING` so CLI users can select `jsonl` or
  `content-length`.
- Added handling for server-initiated `roots/list` requests, which the current
  official filesystem server can send before returning a tool result.

Verification:

```bash
python -m pytest tests/test_mcp_client.py -q
```

## Session 3 - Red-Team Finding: Ambiguous Direct Filesystem Boundary

Prompt/context:

```text
The SPEC says file operations should go through MCP, but operations.py used
os.path helpers. Some path normalization is acceptable; direct file I/O is not.
```

AI output summary:

- Define a clear boundary: client-side path normalization and workspace checks
  are allowed; file reads/writes/listing/moving must go through MCP tool calls.
- Add tests that fail if direct file operations are used in the operations
  layer.

Accepted:

- `FileOperations._resolve_path()`
- workspace root enforcement through `client.allowed_paths`
- monkeypatch tests proving create/move use MCP calls instead of direct file I/O

Rejected:

- Trusting the server alone without a client-side allowlist. A CLI should fail
  early when the requested path is outside the configured workspace.

Manual changes:

- Defaulted the workspace root to the current directory when no
  `MCP_SERVER_PATH` is provided, making examples work from a fresh clone.

Verification:

```bash
python -m pytest tests/test_operations_unit.py -q
```

## Session 4 - Red-Team Finding: Documentation Overclaim

Prompt/context:

```text
The repo claimed 100% Week 1 completion while Sprint 2 tests, release, demo, and
human peer-review were missing.
```

AI output summary:

- Change status language from "100% complete" to "review-ready with explicit
  remaining human evidence."
- Add root README links to the live API and exact verification commands.
- Add `PROCESS-CAVEAT.md`, `EVIDENCE-MANIFEST.md`, and Sprint 2 peer-review
  notes.

Accepted:

- Honest status language.
- Public URL evidence.
- Free-tier persistence caveat.
- Sprint 2 adversarial review matrix.

Rejected:

- Faking past two-hour commit cadence.
- Claiming a human demo video or human peer review before those exist.

Manual changes:

- The final report keeps the strict-pass blockers visible so the repo is
  credible under adversarial review.

Verification:

Run a repo-wide search for stale completion phrases and obsolete deployment
claims.

Expected result:

```text
No stale overclaim in final status sections.
```
