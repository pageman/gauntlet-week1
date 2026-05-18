# Week 1 Evidence Manifest

| Requirement | Evidence | Verification | Status |
| --- | --- | --- | --- |
| Sprint 1 REST API with 5+ CRUD endpoints | `sprint1-api/app/main.py` | Inspect FastAPI routes | Done |
| Sprint 1 public URL | `https://gauntlet-week1.onrender.com/health` | `curl -fsS .../health` | Done |
| Sprint 1 live stress checks | `LIVE-STRESS-RESULTS.md` | Inspect 25-check summary | Done |
| Sprint 1 endpoint tests | `sprint1-api/tests/test_api.py` | `cd sprint1-api && python -m pytest tests -q` (`42 passed`) | Done |
| Sprint 1 Python 3.12 deprecation check | `sprint1-api/app/database.py`, `sprint1-api/app/main.py` | `PYTHONWARNINGS=error::DeprecationWarning python -m pytest tests -q` | Done |
| Sprint 1 progressive security hardening | `sprint1-api/app/main.py`, `sprint1-api/app/database.py` | Auth/rate-limit/sort/tag/corrupt-row tests in `test_api.py` | Done |
| Sprint 1 deployment docs | `sprint1-api/DEPLOYMENT-GUIDE.md`, `sprint1-api/render.yaml` | Inspect docs/config | Done |
| Sprint 1 AI log | `sprint1-api/AI-INTERACTION-LOG.md` | Inspect accepted/rejected/tested notes | Done |
| Sprint 1 peer review notes | `sprint1-api/PEER-REVIEW-NOTES.md` | Inspect notes | Done |
| Sprint 2 MCP CLI implementation | `sprint2-cli/src/mcpfs/` | Inspect code | Done |
| Sprint 2 MCP stdio framing | `sprint2-cli/src/mcpfs/mcp_client.py` | `python -m pytest tests/test_mcp_client.py -q` | Done |
| Sprint 2 official MCP smoke | `sprint2-cli/README.md` | `mcpfs read README.md --lines 5` with `npx -y @modelcontextprotocol/server-filesystem` | Done |
| Sprint 2 test suite | `sprint2-cli/tests/` | `cd sprint2-cli && python -m pytest tests -q` (`38 passed`) | Done |
| Sprint 2 progressive security hardening | `sprint2-cli/src/mcpfs/`, `sprint2-cli/tests/` | Path/MCP/env/bounds/glob/UTF-8 tests | Done |
| Sprint 2 AI log | `sprint2-cli/AI-INTERACTION-LOG.md` | Inspect log | Done |
| Sprint 2 adversarial review | `sprint2-cli/PEER-REVIEW-NOTES.md` | Inspect comment/response matrix | Done as AI review |
| Human Sprint 2 peer review | Not yet attached | PR with five human comments/responses | Pending human follow-up |
| Demo video | `https://youtu.be/8-ADXN3AItI`, `https://youtu.be/-3tBRgHGyBQ` | Links in README | Done |
| Manual CI workaround | `scripts/manual-ci.sh`, `MANUAL-CI-EVIDENCE.md`, `Makefile` | `bash scripts/manual-ci.sh` | Done |
| Process caveat | `PROCESS-CAVEAT.md` | Inspect file | Done |

## Scoring Interpretation

This repo is now a strong Week 1 repair, but a strict 100/100 still depends on
human evidence that cannot be manufactured honestly inside the codebase:

- human peer-review comments and responses,
- future real-time commit cadence.
