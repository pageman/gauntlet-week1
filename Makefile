PYTHON ?= python3

.PHONY: check-python setup bootstrap setup-sprint1 setup-sprint2 test test-sprint1 test-sprint2 live-smoke

check-python:
	$(PYTHON) -c "import sys; v=sys.version_info; raise SystemExit(0 if (3, 11) <= v[:2] < (3, 13) else 'Python 3.11 or 3.12 required for this pinned Week 1 dependency set')"

setup: check-python bootstrap setup-sprint1 setup-sprint2

bootstrap:
	$(PYTHON) -m pip install --upgrade pip

setup-sprint1:
	cd sprint1-api && $(PYTHON) -m pip install -r requirements.txt

setup-sprint2:
	cd sprint2-cli && $(PYTHON) -m pip install -e ".[dev]"

test: check-python test-sprint1 test-sprint2

test-sprint1:
	cd sprint1-api && $(PYTHON) -m pytest tests -q

test-sprint2:
	cd sprint2-cli && $(PYTHON) -m pytest tests -q

live-smoke:
	curl -fsS https://gauntlet-week1.onrender.com/health
	curl -fsS https://gauntlet-week1.onrender.com/api/v1/tasks
	curl -fsS https://gauntlet-week1.onrender.com/api/v1/tasks/stats
