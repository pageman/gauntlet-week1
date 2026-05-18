# Manual CI Evidence

GitHub Actions is not required for this Week 1 evidence package. The repository
uses a manual verification path because GitHub reported that Actions jobs could
not start while the account was locked due to a billing issue.

## Primary Command

Run this from the repository root with Python 3.11 or 3.12:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
bash scripts/manual-ci.sh
```

Optional official MCP server smoke:

```bash
RUN_OFFICIAL_MCP_SMOKE=1 bash scripts/manual-ci.sh
```

## What Manual CI Covers

| Check | Command path | Expected result |
| --- | --- | --- |
| Sprint 1 setup | `sprint1-api/requirements.txt` | dependencies install |
| Sprint 1 tests | `python -m pytest tests -q` in `sprint1-api/` | `36 passed` |
| Sprint 2 setup | `pip install -e ".[dev]"` in `sprint2-cli/` | package installs |
| Sprint 2 tests | `python -m pytest tests -q` in `sprint2-cli/` | `24 passed` |
| Official MCP smoke | `mcpfs read README.md --lines 5` | README preview appears |
| Live API smoke | `curl /health`, `/api/v1/tasks`, `/api/v1/tasks/stats` | JSON responses |
| Python 3.12 deprecation check | `PYTHONWARNINGS=error::DeprecationWarning python -m pytest tests -q` in `sprint1-api/` | `36 passed` |

## Latest Verified Results

Date: 2026-05-18 13:20:19 PST

Command:

```bash
PYTHON=/private/tmp/gauntlet-manual-ci-venv/bin/python RUN_SETUP=0 RUN_OFFICIAL_MCP_SMOKE=1 bash scripts/manual-ci.sh
```

Result:

```text
manual CI: completed
sprint1-api: 36 passed
sprint2-cli: 24 passed
official MCP smoke: README preview returned through npx @modelcontextprotocol/server-filesystem
Python 3.12 deprecation check: 36 passed with DeprecationWarning treated as an error
```

Live API smoke:

```json
{"status":"healthy","timestamp":"2026-05-18T05:19:15.067972","version":"1.0.0"}
{"tasks":[],"total":0,"page":1,"per_page":20,"total_pages":0}
{"total_tasks":0,"by_status":{},"by_priority":{}}
```

## Reviewer Instructions

If GitHub Actions is unavailable, use this file as the CI evidence index:

1. Run `bash scripts/manual-ci.sh`.
2. Copy the terminal output into a GitHub Issue titled `Manual CI Evidence`.
3. Link that issue from the final Week 1 report or peer-review response.
4. If the live smoke is slow, note Render Free cold-start behavior rather than
   treating the delay as a functional failure.
