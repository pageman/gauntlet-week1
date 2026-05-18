# Gauntlet Week 1 Evidence Package

This repository is a Week 1 evidence package for the Beyond Vibe Code
Gauntlet. It contains:

- `sprint1-api/`: deployed FastAPI task-management REST API
- `sprint2-cli/`: MCP-integrated filesystem CLI
- `WEEK1-REPORT.md`: current status, score, remaining strict-pass blockers
- `EVIDENCE-MANIFEST.md`: requirement-to-proof map
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

## Current Strict-Gauntlet Status

This repo is now appropriate for adversarial peer review. It should not claim a
perfect strict Week 1 pass until these human/process artifacts are attached:

- a real 3-minute demo video link,
- a human Sprint 2 peer review with at least five comments and responses,
- a real-time atomic commit cadence in future weeks.

Everything else that can be repaired in-repo has been made explicit, tested, or
documented.
