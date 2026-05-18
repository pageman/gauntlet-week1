#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON:-python3.11}"
BASE_URL="${BASE_URL:-https://gauntlet-week1.onrender.com}"
RUN_SETUP="${RUN_SETUP:-1}"
RUN_LIVE_SMOKE="${RUN_LIVE_SMOKE:-1}"
RUN_OFFICIAL_MCP_SMOKE="${RUN_OFFICIAL_MCP_SMOKE:-0}"

echo "== Manual CI for Gauntlet Week 1 =="
echo "Root: ${ROOT_DIR}"
echo "Python: ${PYTHON_BIN}"

"${PYTHON_BIN}" -c "import sys; v=sys.version_info; raise SystemExit(0 if (3, 11) <= v[:2] < (3, 13) else 'Python 3.11 or 3.12 required for this pinned Week 1 dependency set')"

if [[ "${RUN_SETUP}" == "1" ]]; then
  echo
  echo "== Setup dependencies =="
  "${PYTHON_BIN}" -m pip install --upgrade pip
  (cd "${ROOT_DIR}/sprint1-api" && "${PYTHON_BIN}" -m pip install -r requirements.txt)
  (cd "${ROOT_DIR}/sprint2-cli" && "${PYTHON_BIN}" -m pip install -e ".[dev]")
fi

echo
echo "== Sprint 1 tests =="
(cd "${ROOT_DIR}/sprint1-api" && "${PYTHON_BIN}" -m pytest tests -q)

echo
echo "== Sprint 2 tests =="
(cd "${ROOT_DIR}/sprint2-cli" && "${PYTHON_BIN}" -m pytest tests -q)

if [[ "${RUN_OFFICIAL_MCP_SMOKE}" == "1" ]]; then
  echo
  echo "== Official MCP filesystem smoke =="
  (cd "${ROOT_DIR}/sprint2-cli" && "${PYTHON_BIN}" -m mcpfs.cli read README.md --lines 5)
fi

if [[ "${RUN_LIVE_SMOKE}" == "1" ]]; then
  echo
  echo "== Live Render API smoke =="
  curl -fsS --max-time 60 "${BASE_URL}/health"
  echo
  curl -fsS --max-time 60 "${BASE_URL}/api/v1/tasks"
  echo
  curl -fsS --max-time 60 "${BASE_URL}/api/v1/tasks/stats"
  echo
fi

echo
echo "Manual CI completed."
