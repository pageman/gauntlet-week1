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

## Sprint 2 Manual Local Verification Flow

Demo video:

```text
https://youtu.be/-3tBRgHGyBQ
```

This recording demonstrates the local Sprint 2 verification path: moving to the
repo root, creating and activating a Python 3.11 virtual environment, installing
`sprint2-cli` in editable mode with test dependencies, and running the Sprint 2
test suite.

Expected terminal result:

```text
38 passed
```

## Week 1 Live API + Sprint 2 CLI Verification Flow

Demo video:

```text
https://youtu.be/8-ADXN3AItI
```

This recording demonstrates the broader Week 1 evidence walkthrough: repo-root
orientation, live Sprint 1 API checks, public `/docs` verification, Sprint 2
test execution, `mcpfs` CLI commands, manual CI evidence, and the evidence
manifest.

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

To include the Python 3.12 deprecation gate, run:

```bash
RUN_PY312_DEPRECATION_CHECK=1 PYTHON312=/path/to/python3.12 bash scripts/manual-ci.sh
```

Committed evidence and instructions live in `MANUAL-CI-EVIDENCE.md`. If a
reviewer wants issue-based proof, copy the script output into a GitHub Issue
titled `Manual CI Evidence` and link it from the review response.

## Current Strict-Gauntlet Status

This repo is now appropriate for adversarial peer review. It should not claim a
perfect strict Week 1 pass until these human/process artifacts are attached:

- a human Sprint 2 peer review with at least five comments and responses,
- a real-time atomic commit cadence in future weeks.

A real demo link is now attached above. Everything else that can be repaired
in-repo has been made explicit, tested, or documented.

## Progressive Security Audit Repair

The repository has also absorbed the progressive security audit from
`gauntlet_week1_progressive_security_audit.md`. The in-repo repairs cover:

- timezone-aware UTC timestamps and warning-free Python 3.12 behavior,
- exact JSON tag filtering and explicit sort-field/sort-order validation,
- safe parsing for malformed stored tags, due dates, and timestamps,
- opt-in write authentication, lightweight rate limiting, CORS origin
  validation, and audit logging for mutating API operations,
- Sprint 2 symlink-aware path containment and sanitized directory-listing
  reconstruction,
- MCP subprocess environment scrubbing, bounded request timeouts, resource
  limits, bounded protocol message reads, and bounded unrelated-message loops,
- safer MCP server command parsing through JSON arrays, shell words, or legacy
  comma form,
- safer file-preview behavior, UTF-8 validation for created content, glob
  pattern validation, and no-direct-filesystem-operation regression tests.

Latest local verification:

```text
Sprint 1: 42 passed
Sprint 2: 38 passed
```

## Research Narrative Arcs and Methodology Arcs

This Week 1 package emerged through a research session that moved from secret
hygiene, to curriculum extraction, to completion-report skepticism, to public
deployment, to adversarial repair, to progressive security hardening. The
overarching narrative arc is a shift from *claims about completion* to
*reviewable evidence of ownership*. The methodological arc is a shift from
generating artifacts to repeatedly asking whether each artifact can survive a
strict reviewer, a live smoke test, a security audit, and an honest process
check.

The controlling rule of the session became:

```text
Do not ask reviewers to trust a claim. Give them an artifact, a command, a URL,
a test result, a transcript, or an explicit caveat.
```

### Arc 1: Exposure To Secret Hygiene

**Narrative/story box:** The session began with a shell startup warning that
printed an Aristotle API key. That turned a small `.zshrc` syntax mistake into
a concrete lesson about secret exposure: a secret is not only at risk when it is
committed; it is also exposed when it appears in shell errors, chat messages,
screenshots, terminal recordings, or logs.

**Method box:** The working heuristic became: set secrets in the form
`export NAME=value`, never add spaces around `=`, never echo the raw value, and
verify with presence checks such as `echo ${NAME:+set}`. If a secret appears in
chat, logs, screenshots, or shell errors, treat it as exposed and rotate it.
Later security work reused the same principle by scrubbing sensitive
environment variables before spawning MCP subprocesses.

### Arc 2: Curriculum Extraction To Artifact Generation

**Narrative/story box:** The work then expanded into extracting the Beyond Vibe
Code curriculum and principles, producing Markdown, LaTeX, PDF, and DOCX
outputs, and organizing deliverables into a dedicated folder. The session moved
from fixing a local configuration issue to building a reproducible research
package.

**Method box:** The method was artifact-first extraction: preserve source
structure, generate portable formats, keep deliverables together, and make the
output inspectable across text, print, and document workflows. The standard was
not "we scraped something"; it was "a reviewer can find the curriculum,
principles, and generated formats without guessing."

### Arc 3: Completion Claims To Evidence Claims

**Narrative/story box:** A generated completion report initially looked
comprehensive, but it collapsed under review because many lessons were filled
with generic database language. The report had coverage-shaped structure but
not lesson-specific substance. That became the first major methodological
correction: completion language is not completion evidence.

**Method box:** The rubric became claim-to-evidence mapping. Every completion
claim should answer: what artifact exists, where is it, how was it tested, what
was rejected or changed, and what still cannot be honestly claimed. Generic
templates are useful only when they are filled with specific code, transcripts,
screenshots, logs, commits, or deployment links.

### Arc 4: Local Practice To Week 1 Evidence Package

**Narrative/story box:** The Week 1 Gauntlet package started as local evidence:
a REST API, an MCP-style CLI, reports, tests, and smoke outputs. Initial scores
improved when the work became more honest about what was missing, but the repo
was still not strict-pass evidence because public deployment, demo evidence,
human review, and process artifacts were incomplete.

**Method box:** The evaluation method separated local-practice evidence from
strict-Gauntlet evidence. Local tests can prove implementation behavior, but
strict review also requires public reachability, demonstration, peer review,
AI/process logs, and honest limitations. This distinction prevented the repo
from overclaiming a perfect pass.

### Arc 5: Public Deployment To External Verification

**Narrative/story box:** Deploying Sprint 1 on Render changed the submission
from "runs locally" to "externally inspectable." The blank root page was
reframed as expected API behavior because the real public proof lives under
`/health`, `/api/v1/tasks`, `/api/v1/tasks/stats`, and `/docs`. The demo
recordings then added human-readable walkthrough evidence for both the live API
and Sprint 2 CLI.

**Method box:** The deployment method was endpoint-first verification. A public
URL counts only when a reviewer can hit concrete endpoints and receive valid
responses. Free-tier behavior was documented rather than hidden: cold starts
can take time, and temporary storage means task data is demo data. The workflow
also separated browser actions from shell commands: URLs are opened in a
browser or checked with `curl`, not executed directly in `zsh`.

### Arc 6: Red-Team Review To Repair Plan

**Narrative/story box:** The adversarial review exposed the gap between
"credible-looking" and "review-ready." Sprint 1 had public proof, but Sprint 2
needed real tests, protocol evidence, AI logs, review notes, packaging clarity,
and a clean ownership trail. The report also overclaimed completion, which was
treated as a process defect rather than wording polish.

**Method box:** The red-team method was to test explicit, implicit, inferred,
extrapolated, and hidden weaknesses. Each finding needed a repair, an acceptance
test, and a before/after interpretation. The repair target was not maximum
optimism; it was reducing the number of claims a strict reviewer could falsify.

### Arc 7: Repair Pass To Review-Ready Evidence Package

**Narrative/story box:** The repair pass converted the repo into a stronger
evidence package: root-level verification commands, manual CI, Sprint 2 tests,
MCP framing support, `roots/list` handling, AI logs, adversarial review notes,
live stress results, demo links, and a process caveat for the reconstructed
commit history.

**Method box:** The repair loop was: identify a falsifiable weakness, patch the
smallest relevant surface, add or update tests, update docs to match the real
state, run local verification, smoke the public service, and push the result.
When GitHub Actions was unavailable, the method changed from "wait for hosted
CI" to "build a manual CI transcript reviewers can reproduce." When the official
MCP server needed a longer `npx` cold-start window, the method changed from
"assume a 30-second timeout is enough" to "make timeout bounded and
configurable."

### Arc 8: Progressive Security Audit To Hardened Evidence

**Narrative/story box:** The progressive security audit shifted the work from
Gauntlet-readiness to adversarial hardening. The audit found issues across
Sprint 1 and Sprint 2: naive UTC timestamps, fragile tag filtering, invalid
sort behavior, optional-field parsing crashes, public write risk, missing rate
limits, CORS looseness, MCP subprocess exposure, path traversal risk, unsafe
glob patterns, unbounded protocol reads, unbounded file previews, and weak
command parsing.

**Method box:** The security methodology was progressive hardening from obvious
warnings to deeper failure modes. Low-hanging fixes closed warning noise and
stale docs. Medium-depth fixes closed logic bugs and path containment issues.
Deeper fixes added default-deny behavior, bounded resource use, subprocess
environment scrubbing, exact validation, and regression tests. The final proof
was not the patch itself; it was the updated verification state: Sprint 1
`42 passed`, Sprint 2 `38 passed`, manual CI passing, Python 3.12 deprecation
checks passing, and official MCP smoke separately verified.

### Arc 9: Remaining Human Evidence

**Narrative/story box:** The final state is intentionally not labeled as
perfect. The repo is now review-ready and materially hardened, but a strict
100/100 still depends on human/process artifacts that cannot be manufactured
inside the codebase: human Sprint 2 review and future real-time commit cadence.
The demo evidence is now linked; the remaining gap is not code functionality,
but external human verification and future process discipline.

**Method box:** The ownership rule is: do not fake process evidence. If evidence
does not exist, disclose it, create the next honest artifact, and link it when
complete. This is the difference between a persuasive portfolio and a
Gauntlet-grade evidence package. The repo should therefore stay labeled as
review-ready, not perfect, until human comments/responses and future cadence
evidence exist.

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
mcpfs read now has bounded preview behavior. Please add or verify one reviewer
transcript showing what happens with a very large file and confirm the output
is truncated without a traceback.
```

Expected response: link the existing regression test and add a short terminal
transcript or screenshot to the review response.

### Issue 4: Make server command parsing safer than comma-splitting

Comment:

```text
MCP_SERVER_CMD now supports JSON arrays, shell words, and the old comma format.
Please verify the README shows the recommended JSON-array form first and keeps
the comma form labeled as a compatibility fallback.
```

Expected response: link the parser tests and the README configuration section.

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
