# -------------------------
# App configuration
# -------------------------
APP_MODULE=app.main:app
HOST?=0.0.0.0
PORT?=8080
LOG_LEVEL?=info
WORKERS?=1

# -------------------------
# Virtual environment
# -------------------------
VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
UVICORN=$(VENV)/bin/uvicorn
RUFF=$(VENV)/bin/ruff
BLACK=$(VENV)/bin/black
PYTEST=$(VENV)/bin/pytest

# -------------------------
# Targets
# -------------------------
.PHONY: help venv install dev run prod lint format test clean

help:
	@echo "Available commands:"
	@echo "  make dev     - Run with auto-reload (development)"
	@echo "  make run     - Run without reload"
	@echo "  make prod    - Run with multiple workers"
	@echo "  make install - Create venv and install dependencies"
	@echo "  make lint    - Run linters"
	@echo "  make format  - Format code"
	@echo "  make test    - Run tests"
	@echo "  make clean   - Remove venv and cache files"

# -------------------------
# Virtualenv setup
# -------------------------
$(VENV)/bin/activate:
	python3 -m venv $(VENV)

install: $(VENV)/bin/activate
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# -------------------------
# Run commands
# -------------------------
dev: install
	PYTHONPATH=. $(UVICORN) $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--reload \
		--log-level $(LOG_LEVEL)

run: install
	PYTHONPATH=. $(UVICORN) $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--log-level $(LOG_LEVEL)

prod: install
	PYTHONPATH=. $(UVICORN) $(APP_MODULE) \
		--host $(HOST) \
		--port $(PORT) \
		--workers $(WORKERS) \
		--log-level $(LOG_LEVEL)

# -------------------------
# Quality
# -------------------------
lint: install
	$(RUFF) app

format: install
	$(BLACK) app

test: install
	$(PYTEST)

# -------------------------
# Cleanup
# -------------------------
clean:
	rm -rf $(VENV) __pycache__ .pytest_cache .ruff_cache
