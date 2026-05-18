# Gauntlet Week 1 Evidence Package

This repository is a Week 1 evidence package for the Beyond Vibe Code
Gauntlet. It contains:

- `sprint1-api/`: deployed FastAPI task-management REST API
- `sprint2-cli/`: MCP-integrated filesystem CLI
- `WEEK1-REPORT.md`: current status, score, remaining strict-pass blockers
- `EVIDENCE-MANIFEST.md`: requirement-to-proof map
- `MANUAL-CI-EVIDENCE.md`: local CI and live-smoke workaround evidence
- `PROCESS-CAVEAT.md`: honest note about reconstructed history

## Live Sprint 1 API

Public base URL:

```text
https://gauntlet-week1.onrender.com
```

Verified endpoints:

```text
https://gauntlet-week1.onrender.com/health
https://gauntlet-week1.onrender.com/api/v1/tasks
https://gauntlet-week1.onrender.com/api/v1/tasks/stats
https://gauntlet-week1.onrender.com/docs
```

Render Free caveat: the service may spin down after inactivity, so first
requests can take 20-30 seconds. The free instance uses temporary storage in
this deployment, so task data is demo data and may reset across restarts.

## Quick Verification

Fresh clone setup:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
make setup
make test
```

If your shell's default `python3` is older than 3.11, run:

```bash
make setup PYTHON=/path/to/python3.11
make test PYTHON=/path/to/python3.11
```

Use Python 3.11 or 3.12 for the combined Week 1 verifier. Sprint 1 pins a
Pydantic version that is not suitable for Python 3.14.

Sprint 1 API, from a Python 3.11 environment:

```bash
cd sprint1-api
python -m pip install -r requirements.txt
python -m pytest tests -q
```

Sprint 2 CLI:

```bash
cd sprint2-cli
python -m pip install -e ".[dev]"
python -m pytest tests -q
```

Public smoke:

```bash
curl -fsS https://gauntlet-week1.onrender.com/health
curl -fsS https://gauntlet-week1.onrender.com/api/v1/tasks
curl -fsS https://gauntlet-week1.onrender.com/api/v1/tasks/stats
```

## Manual CI, No GitHub Actions Required

GitHub Actions is intentionally not required for this submission because the
account could not start Actions jobs while locked by a billing issue. The repo
therefore uses a manual CI workaround that a reviewer can run and audit.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
bash scripts/manual-ci.sh
```

The manual CI script installs dependencies, runs both Sprint test suites, and
smokes the public Render API. To include the optional official MCP filesystem
server smoke, run:

```bash
RUN_OFFICIAL_MCP_SMOKE=1 bash scripts/manual-ci.sh
```

Committed evidence and instructions live in `MANUAL-CI-EVIDENCE.md`. If a
reviewer wants issue-based proof, copy the script output into a GitHub Issue
titled `Manual CI Evidence` and link it from the review response.

## Current Strict-Gauntlet Status

This repo is now appropriate for adversarial peer review. It should not claim a
perfect strict Week 1 pass until these human/process artifacts are attached:

- a real 3-minute demo video link,
- a human Sprint 2 peer review with at least five comments and responses,
- a real-time atomic commit cadence in future weeks.

Everything else that can be repaired in-repo has been made explicit, tested, or
documented.

## Research Narrative Arcs and Methodology Arcs

This Week 1 package was produced through a research session that moved from
secret hygiene, to curriculum extraction, to evidence assessment, to public
deployment, to adversarial repair. The main lesson of the session is that a
credible Gauntlet submission is not a polished story about completion; it is a
traceable chain of claims, artifacts, tests, deployments, reviews, and honest
caveats.

### Arc 1: Exposure To Secret Hygiene

**Story box:** The session began with a shell startup warning that exposed an
Aristotle API key in terminal output. The practical story was not just "hide
the key"; it was learning why shell configuration syntax matters, why secrets
should not appear in logs, and how to verify an environment variable without
printing its value.

**Method box:** The working heuristic became: set secrets in the form
`export NAME=value`, never add spaces around `=`, never echo the raw value, and
verify with presence checks such as `echo ${NAME:+set}`. If a secret appears in
chat, logs, screenshots, or shell errors, treat it as exposed and rotate it.

### Arc 2: Curriculum Extraction To Artifact Generation

**Story box:** The work then expanded into extracting the Beyond Vibe Code
curriculum and principles, producing Markdown, LaTeX, PDF, and DOCX outputs,
and organizing deliverables into a dedicated folder. That shifted the session
from one-off troubleshooting into reproducible research packaging.

**Method box:** The method was artifact-first extraction: preserve source
structure, generate portable formats, keep deliverables together, and make the
output inspectable across text, print, and document workflows. The standard was
not "we scraped something"; it was "a reviewer can find the curriculum,
principles, and generated formats without guessing."

### Arc 3: Completion Claims To Evidence Claims

**Story box:** A generated completion report initially looked comprehensive but
collapsed under review because many lessons were filled with generic database
language. The narrative turned from "coverage exists" to "coverage must be
lesson-specific and evidence-backed."

**Method box:** The rubric became claim-to-evidence mapping. Every completion
claim should answer: what artifact exists, where is it, how was it tested, what
was rejected or changed, and what still cannot be honestly claimed. Generic
templates are useful only when they are filled with specific code, transcripts,
screenshots, logs, commits, or deployment links.

### Arc 4: Local Practice To Public Deployment

**Story box:** The Week 1 Gauntlet package started as local evidence: a REST API,
an MCP-style CLI, reports, tests, and smoke outputs. The public deployment on
Render changed the submission from "runs on my machine" to "externally
inspectable." The blank root page was clarified as expected API behavior because
the live proof lives under `/health`, `/api/v1/tasks`, `/api/v1/tasks/stats`,
and `/docs`.

**Method box:** The deployment method was endpoint-first verification. A public
URL counts only when a reviewer can hit concrete endpoints and receive valid
responses. Free-tier behavior was documented rather than hidden: cold starts can
take time, and temporary storage means task data is demo data.

### Arc 5: Red-Team Review To Repair Plan

**Story box:** The adversarial review exposed the gap between "credible-looking"
and "review-ready." Sprint 1 had public proof, but Sprint 2 lacked tests,
stronger protocol evidence, peer review, and a clean ownership trail. The report
also overclaimed completion, which was treated as a process defect rather than
wording polish.

**Method box:** The red-team method was to test explicit, implicit, inferred,
extrapolated, and hidden weaknesses. Each finding needed a repair, an acceptance
test, and a before/after interpretation. The repair target was not maximum
optimism; it was reducing the number of claims a strict reviewer could falsify.

### Arc 6: Repair Pass To Review-Ready Evidence Package

**Story box:** The repair pass converted the repo into a stronger evidence
package: root-level verification commands, manual CI, Sprint 2 tests, MCP
framing support, `roots/list` handling, AI logs, adversarial review notes, live
stress results, and a process caveat for the reconstructed commit history.

**Method box:** The repair loop was: identify a falsifiable weakness, patch the
smallest relevant surface, add or update tests, update docs to match the real
state, run local verification, smoke the public service, and push the result.
When the official MCP server contradicted an assumption about framing, the
method changed from "defend the first fix" to "support the real server and test
both modes."

### Arc 7: Remaining Human Evidence

**Story box:** The final state is intentionally not labeled as perfect. The repo
is appropriate for adversarial peer review, but a strict 100/100 still requires
human/process artifacts that cannot be manufactured inside the codebase:
recorded demo, human Sprint 2 review, and future real-time commit cadence.

**Method box:** The ownership rule is: do not fake process evidence. If evidence
does not exist, disclose it, create the next honest artifact, and link it when
complete. This is the difference between a persuasive portfolio and a
Gauntlet-grade evidence package.

## Human Sprint 2 Peer Review Issue Starters

These are low-hanging review comments that a human reviewer can file as GitHub
Issues or PR comments for `sprint2-cli/`. They should not be marked as completed
human peer review until a real person files or endorses them and the response
links to the relevant patch, test, or explicit non-change decision.

### Issue 1: Add an official MCP compatibility transcript

Comment:

```text
Sprint 2 now supports the official filesystem server, but the repo should show
an exact transcript for one real run against npx @modelcontextprotocol/server-filesystem.
Please add the command, environment, output, and expected result so reviewers do
not have to infer official-server compatibility from the test suite alone.
```

Expected response: add a short transcript to Sprint 2 docs or evidence notes,
then link it from `EVIDENCE-MANIFEST.md`.

### Issue 2: Document supported MCP stdio framing modes more visibly

Comment:

```text
The client supports JSONL and Content-Length framing, but a reviewer may not
know when to use each mode. Please add a small compatibility table showing
which mode is default, which server it was tested against, and how to override
MCP_STDIO_FRAMING.
```

Expected response: update `sprint2-cli/README.md` with a framing compatibility
table and keep the protocol tests linked.

### Issue 3: Add a guard for huge or binary file previews

Comment:

```text
mcpfs read currently displays text returned by the server, but the CLI does not
clearly protect the terminal from very large or binary-like output. Please add
a max-byte or max-character preview guard, or document why line limiting is the
Week 1 boundary.
```

Expected response: either implement a bounded preview option or add a clear
known limitation with a Week 2 follow-up issue.

### Issue 4: Make server command parsing safer than comma-splitting

Comment:

```text
MCP_SERVER_CMD is split on commas. That is simple, but it can break if a path or
argument contains a comma. Please consider JSON-array parsing, shlex parsing, or
a documented limitation with examples.
```

Expected response: patch `get_mcp_client()` to accept a JSON array first, with
comma-splitting kept only as a compatibility fallback, or document the tradeoff.

### Issue 5: Add CLI package/release instructions

Comment:

```text
Sprint 2 is source-installable with pip install -e, but strict review asks for
a packageable or releasable CLI. Please add the exact build command and release
steps, even if the GitHub release itself is still pending.
```

Expected response: add `python -m build` instructions, release checklist, and
the artifact names a reviewer should expect.

### Issue 6: Add a negative test for unsupported MCP tools

Comment:

```text
The client translates tool errors, but I would like one explicit test proving an
unknown or unsupported MCP tool returns an actionable error without a traceback.
That is an easy regression test for the CLI ownership claim.
```

Expected response: add a test that forces an unsupported tool response and
asserts exit code, message, and no traceback.

### Issue 7: Clarify human-vs-AI review status

Comment:

```text
The repo includes adversarial AI-assisted review notes, which are useful, but
strict Gauntlet review requires human peer review. Please add a small table
separating AI-assisted review, self-review, and human review status so this is
impossible to misread.
```

Expected response: update `sprint2-cli/PEER-REVIEW-NOTES.md` or the root README
with a status table and leave the human-review item pending until a person
actually comments.
