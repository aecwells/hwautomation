# Streamlined Makefile for HWAutomation
# Focus on essential development and deployment tasks

# ---------------------------
# Configurable variables
# ---------------------------
PROJECT_NAME ?= hwautomation
ENV_FILE ?= .env
SERVICE ?= app
COMPOSE_YML := docker-compose.yml
COMPOSE_OVERRIDE := docker-compose.override.yml
DOCKER_COMPOSE := docker compose

# Use bash with strict flags for safer Makefile recipes
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Centralized docker-compose invocation
COMPOSE_CMD := $(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME)

# Compose files (include override if present)
ifeq ($(wildcard $(COMPOSE_OVERRIDE)),)
  COMPOSE_FILES := -f $(COMPOSE_YML)
else
  COMPOSE_FILES := -f $(COMPOSE_YML) -f $(COMPOSE_OVERRIDE)
endif

# Git-related
GIT_COMMIT ?= $(shell git rev-parse --short HEAD)
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
VERSION ?= $(shell git describe --tags --always --dirty)

.DEFAULT_GOAL := help
.PHONY: help test test-unit test-cov clean-test docs build up down restart shell dev-setup

## [General]
## Show this help message
help:
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "}; \
		/^## \[.*\]$$/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 4)} \
		/^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

## [Development Environment]
dev-setup:       ## Setup complete development environment
	@echo "Setting up development environment..."
	cp .env.example .env || echo "Create .env file manually"
	mkdir -p data logs
	@echo "Installing Python dependencies..."
	source hwautomation-env/bin/activate && pip install -e .[dev]
	@echo "Installing frontend dependencies..."
	npm install
	@echo "Building frontend assets..."
	npm run build
	@echo "Development environment ready!"

venv-activate:   ## Show command to activate virtual environment
	@echo "Run: source hwautomation-env/bin/activate"

## [Testing]
test:            ## Run all tests locally
	@if [ -f "hwautomation-env/bin/activate" ]; then \
		source hwautomation-env/bin/activate && pytest; \
	else \
		pytest; \
	fi

test-unit:       ## Run unit tests only (fast)
	@if [ -f "hwautomation-env/bin/activate" ]; then \
		source hwautomation-env/bin/activate && pytest tests/unit/ -m "not slow"; \
	else \
		pytest tests/unit/ -m "not slow"; \
	fi

test-cov:        ## Run tests with coverage
	@if [ -f "hwautomation-env/bin/activate" ]; then \
		bash -c "cd $(PWD) && source hwautomation-env/bin/activate && pytest --cov=src/hwautomation --cov-report=term-missing --cov-report=xml"; \
	else \
		pytest --cov=src/hwautomation --cov-report=term-missing --cov-report=xml; \
	fi

test-html:       ## Generate HTML coverage report
	@if [ -f "hwautomation-env/bin/activate" ]; then \
		source hwautomation-env/bin/activate && pytest --cov=src/hwautomation --cov-report=html; \
	else \
		pytest --cov=src/hwautomation --cov-report=html; \
	fi
	@echo "Coverage report generated in htmlcov/index.html"

clean-test:      ## Clean test artifacts and cache
	rm -rf .pytest_cache/ htmlcov/ .coverage coverage.xml
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

## [Code Quality]
format:          ## Format code with black and isort
	@if [ -f "hwautomation-env/bin/activate" ]; then \
		source hwautomation-env/bin/activate && black src/ tests/ && isort src/ tests/; \
	else \
		black src/ tests/ && isort src/ tests/; \
	fi

lint:            ## Run linting checks
	@if [ -f "hwautomation-env/bin/activate" ]; then \
		source hwautomation-env/bin/activate && flake8 src/ tests/; \
	else \
		flake8 src/ tests/; \
	fi

quality-check:   ## Run all code quality checks (format, lint)
	@if [ -f "hwautomation-env/bin/activate" ]; then \
		source hwautomation-env/bin/activate && black --check src/ tests/ && isort --check-only src/ tests/ && flake8 src/ tests/; \
	else \
		black --check src/ tests/ && isort --check-only src/ tests/ && flake8 src/ tests/; \
	fi

## [Documentation]
docs:            ## Build Sphinx HTML documentation
	@echo "Building Sphinx documentation..."
	cd docs && make html
	@echo "Documentation built in docs/_build/html/"

docs-serve:      ## Build and serve documentation locally
	@echo "Building and serving documentation..."
	cd docs && make serve

docs-clean:      ## Clean documentation build artifacts
	@echo "Cleaning documentation build artifacts..."
	cd docs && make clean

## [Frontend]
frontend-build:  ## Build frontend assets
	@if [ ! -d "node_modules" ]; then \
		echo "Installing frontend dependencies..."; \
		npm ci; \
	fi
	npm run build

frontend-dev:    ## Start frontend development server
	@if [ ! -d "node_modules" ]; then \
		echo "Installing frontend dependencies..."; \
		npm ci; \
	fi
	npm run dev

frontend-clean:  ## Clean frontend build artifacts
	npm run clean

## [Docker Services]
build:           ## Build Docker images (includes frontend)
	@echo "Building frontend assets..."
	@npm run build
	@echo "Building docker images..."
	$(COMPOSE_CMD) build

up:              ## Start containers in background
	$(COMPOSE_CMD) up -d

down:            ## Stop and remove containers, networks, volumes
	$(COMPOSE_CMD) down

restart:         ## Restart containers
	$(MAKE) down
	$(MAKE) up

ps:              ## List running containers
	$(COMPOSE_CMD) ps

logs:            ## Tail logs from all services
	$(COMPOSE_CMD) logs -f

shell:           ## Open a shell in the default service (SERVICE=app)
	$(COMPOSE_CMD) exec $(SERVICE) sh

## [Data Management]
data-backup:     ## Backup database files
	@mkdir -p data/backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	if [ -f data/hw_automation.db ]; then \
		cp data/hw_automation.db data/backups/hw_automation_$$timestamp.db; \
		echo "Backed up database to data/backups/hw_automation_$$timestamp.db"; \
	else \
		echo "No database found to backup"; \
	fi

data-clean:      ## Clean old backup files (keep last 10)
	@find data/backups -name "*.db" -type f | sort -r | tail -n +11 | xargs rm -f || true
	@echo "Cleaned old database backups"

## [Release Management]
changelog:       ## Generate CHANGELOG.md from git commits
	source hwautomation-env/bin/activate && python3 tools/generate_changelog.py

version:         ## Show current version
	@python3 -c "import re; content=open('pyproject.toml').read(); print(re.search(r'version\\s*=\\s*\"([^\"]+)\"', content).group(1))"

## [Debug]
debug:           ## Print debug variables
	@echo "PWD=$(PWD)"
	@echo "ENV_FILE=$(ENV_FILE)"
	@echo "PROJECT_NAME=$(PROJECT_NAME)"
	@echo "COMPOSE_FILES=$(COMPOSE_FILES)"
	@echo "SERVICE=$(SERVICE)"
	@echo "GIT_COMMIT=$(GIT_COMMIT)"
	@echo "GIT_BRANCH=$(GIT_BRANCH)"
	@echo "VERSION=$(VERSION)"
