# Week 1 Demo Script

This is a script for the required 3-minute demo video. The actual video still
needs to be recorded and linked from `README.md` and `WEEK1-REPORT.md`.

## Sprint 1 API Demo

1. Open `https://gauntlet-week1.onrender.com/docs`.
2. Show `GET /health`.
3. Run:

```bash
curl -fsS https://gauntlet-week1.onrender.com/health
```

4. Create a task:

```bash
curl -sS -X POST https://gauntlet-week1.onrender.com/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demo task","description":"Created during demo","priority":"medium"}'
```

5. List tasks:

```bash
curl -fsS https://gauntlet-week1.onrender.com/api/v1/tasks
```

6. Show validation failure:

```bash
curl -i -X POST https://gauntlet-week1.onrender.com/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":""}'
```

7. Show `sprint1-api/tests/test_api.py`.
8. Show `sprint1-api/AI-INTERACTION-LOG.md`.
9. State the free-tier caveat: cold starts and temporary data.

## Sprint 2 CLI Demo

1. Open `sprint2-cli/SPEC.md`.
2. Install:

```bash
cd sprint2-cli
python -m pip install -e ".[dev]"
```

3. Run tests:

```bash
python -m pytest tests -q
```

4. Explain MCP stdio framing in `src/mcpfs/mcp_client.py`.
5. Show the fake MCP server tests.
6. State the human-review caveat: adversarial review exists, human PR review
   still needs to be attached for a strict pass.
