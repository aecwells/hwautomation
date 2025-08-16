# Makefile for HWAutomation with Docker Compose support and testing

# ---------------------------
# Configurable variables
# ---------------------------
PROJECT_NAME ?= hwautomation
ENV_FILE ?= .env
SERVICE ?= app
TARGET ?= app
COMPOSE_YML := docker-compose.yml
COMPOSE_OVERRIDE := docker-compose.override.yml
DOCKER_COMPOSE := docker compose

# Use bash with strict flags for safer Makefile recipes
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Centralized docker-compose invocation to avoid repetition
COMPOSE_CMD := $(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME)

# Compose files (include override if present)
ifeq ($(wildcard $(COMPOSE_OVERRIDE)),)
  COMPOSE_FILES := -f $(COMPOSE_YML)
else
  COMPOSE_FILES := -f $(COMPOSE_YML) -f $(COMPOSE_OVERRIDE)
endif

# Git-related
REPO ?= $(shell git config --get remote.origin.url)
GIT_COMMIT ?= $(shell git rev-parse --short HEAD)
GIT_BRANCH ?= $(shell git rev-parse --abbrev-ref HEAD)
VERSION ?= $(shell git describe --tags --always --dirty)
TAG ?= $(VERSION)

# Other info
MAKEPATH ?= $(MAKEFILE_LIST)
PWD := $(shell pwd)

.DEFAULT_GOAL := help
.PHONY: help test test-unit test-integration test-cov test-html clean-test up down restart build pull ps logs shell ci-build ci-test ci-clean

## [General]
## Show this help message
help:
	@echo ""
	@echo "Available targets:"
	@awk 'BEGIN {FS = ":.*?## "}; \
		/^## \[.*\]$$/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 4)} \
		/^[a-zA-Z_-]+:.*##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

## [Frontend Build]
frontend-install: ## Install frontend dependencies
	npm install

frontend-build:   ## Build frontend assets
	npm run build

frontend-dev:     ## Start frontend development server
	npm run dev

frontend-watch:   ## Watch frontend files for changes
	npm run watch

frontend-clean:   ## Clean frontend build artifacts
	npm run clean

frontend-lint:    ## Lint frontend code
	npm run lint

frontend-format:  ## Format frontend code
	npm run format

## [Testing - Local]
# Run all tests
test:         ## Run all tests locally
	pytest

# Run only unit tests (fast)
test-unit:    ## Run unit tests only (fast)
	pytest tests/unit/ -m "not slow"

# Run integration tests
test-integration: ## Run integration tests
	pytest tests/integration/ -m integration

# Run tests with coverage
test-cov:     ## Run tests with coverage report
	pytest --cov=src/hwautomation --cov-report=term-missing

# Generate HTML coverage report
test-html:    ## Generate HTML coverage report
	pytest --cov=src/hwautomation --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Run tests in parallel (faster)
test-parallel: ## Run tests in parallel
	pytest -n auto

# Run async tests specifically
test-async:   ## Run async tests with pytest-asyncio
	pytest -m asyncio

# Run performance tests
test-performance: ## Run performance tests (requires RUN_PERFORMANCE_TESTS=1)
	RUN_PERFORMANCE_TESTS=1 pytest -m "performance"

# Run security scanning
test-security: ## Run security scanning with bandit
	bandit -r src/ -f json -o bandit-report.json || true
	@echo "Security report generated in bandit-report.json"

# Run all quality checks (like pre-commit)
test-quality: ## Run all code quality checks
	black --check src/ tests/
	isort --check-only src/ tests/
	flake8 src/ tests/
	mypy src/
	bandit -r src/

# Clean test artifacts
clean-test:   ## Clean test artifacts and cache
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +

# Install test dependencies
install-test: ## Install development dependencies
	pip install -e .[dev]

# Setup pre-commit hooks
setup-precommit: ## Install and setup pre-commit hooks
	pre-commit install
	pre-commit autoupdate

# Run pre-commit on all files
precommit-all: ## Run pre-commit hooks on all files
	pre-commit run --all-files

## [Documentation]
docs:         ## Build Sphinx HTML documentation
	@echo "Building Sphinx documentation..."
	cd docs && make html
	@echo "Documentation built in docs/_build/html/"

docs-serve:   ## Build and serve documentation locally
	@echo "Building and serving documentation..."
	cd docs && make serve

docs-clean:   ## Clean documentation build artifacts
	@echo "Cleaning documentation build artifacts..."
	cd docs && make clean

docs-apidoc:  ## Generate API documentation from source code
	@echo "Generating API documentation..."
	cd docs && make apidoc

docs-rebuild: ## Clean and rebuild documentation
	@echo "Rebuilding documentation..."
	cd docs && make rebuild

## [Docker Compose]
build:        ## Build the Docker images (includes frontend)
	@echo "Building frontend assets..."
	@npm ci --silent || npm install --silent
	@npm run build
	@echo "Building docker images..."
	$(COMPOSE_CMD) build

 up:           ## Start containers in background
	$(COMPOSE_CMD) up -d

 down:         ## Stop and remove containers, networks, volumes
	$(COMPOSE_CMD) down

 restart:      ## Restart containers
	$(MAKE) down
	$(MAKE) up

# Convenience: build without cache
build-no-cache: ## Build docker images without cache
	@npx --yes npm@latest run build || true
	@echo "Building docker images (no cache)..."
	$(COMPOSE_CMD) build --no-cache

pull:         ## Pull the latest images
	$(COMPOSE_CMD) pull

ps:           ## List running containers
	$(COMPOSE_CMD) ps

logs:         ## Tail logs from all services
	$(COMPOSE_CMD) logs -f

shell:        ## Open a shell in the default service (SERVICE=app)
	$(COMPOSE_CMD) exec $(SERVICE) sh

sh: shell     ## Alias for `make shell`

shell-%:      ## Open a shell in specific service: make shell-maas or shell-db
	$(COMPOSE_CMD) exec $* sh

# Run an arbitrary command in the service: make run-cmd CMD="bash -lc 'echo hi'"
run-cmd:      ## Run an arbitrary command in the default service: make run-cmd CMD="..."
	@if [ -z "$(CMD)" ]; then echo "Usage: make run-cmd CMD=\"your command\"" && exit 1; fi
	$(COMPOSE_CMD) exec $(SERVICE) sh -c "$(CMD)"

# Tag built image with git commit/branch (requires image built locally)
tag:          ## Tag service image with git commit and optional TAG (TAG defaults to VERSION)
	@echo "Tagging images with $(TAG)"
	@# This assumes service image name is $(PROJECT_NAME)_$(SERVICE)
	@docker image tag $(PROJECT_NAME)_$(SERVICE):latest $(PROJECT_NAME)/$(SERVICE):$(TAG) || true

## [Testing - Docker]
test-docker:  ## Run all tests inside Docker container
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $(SERVICE) pytest

test-docker-unit: ## Run unit tests inside Docker container
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $(SERVICE) pytest tests/unit/ -m "not slow"

test-docker-cov: ## Run tests with coverage inside Docker container
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $(SERVICE) pytest --cov=src/hwautomation --cov-report=term-missing

## [Debug]
debug:        ## Print debug variables
	@echo "PWD=$(PWD)"
	@echo "MAKEPATH=$(MAKEPATH)"
	@echo "ENV_FILE=$(ENV_FILE)"
	@echo "PROJECT_NAME=$(PROJECT_NAME)"
	@echo "COMPOSE_FILES=$(COMPOSE_FILES)"
	@echo "SERVICE=$(SERVICE)"
	@echo "TARGET=$(TARGET)"
	@echo "REPO=$(REPO)"
	@echo "GIT_COMMIT=$(GIT_COMMIT)"
	@echo "GIT_BRANCH=$(GIT_BRANCH)"
	@echo "VERSION=$(VERSION)"
	@echo "TAG=$(TAG)"

## [CI/CD]
ci-build:     ## CI build task
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) build

ci-test:      ## CI test task with coverage
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) run --rm $(SERVICE) pytest --cov=src/hwautomation --cov-report=xml

ci-clean:     ## CI cleanup task
	$(DOCKER_COMPOSE) $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) down -v --remove-orphans

## [Development]
dev-setup:    ## Setup development environment
	cp .env.example .env || echo "Create .env file manually"
	mkdir -p data logs
	npm install
	pip install -e .[dev]
	$(MAKE) build

dev-reset:    ## Reset development environment
	$(MAKE) ci-clean
	$(MAKE) clean-test
	$(MAKE) frontend-clean
	$(MAKE) dev-setup

## [Data Management]
data-backup:  ## Backup database files
	@mkdir -p data/backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	if [ -f data/hw_automation.db ]; then \
		cp data/hw_automation.db data/backups/hw_automation_$$timestamp.db; \
		echo "Backed up database to data/backups/hw_automation_$$timestamp.db"; \
	else \
		echo "No database found to backup"; \
	fi

data-clean:   ## Clean old backup files (keep last 10)
	@find data/backups -name "*.db" -type f | sort -r | tail -n +11 | xargs rm -f || true
	@echo "Cleaned old database backups"

data-init:    ## Initialize data directories
	mkdir -p data/{backups,exports,temp} logs
	@echo "Initialized data directories"

## [Release & Changelog]
changelog:    ## Generate CHANGELOG.md from git commits
	python3 tools/generate_changelog.py

changelog-since: ## Generate changelog since specific tag (usage: make changelog-since TAG=v1.0.0)
	python3 tools/generate_changelog.py --since $(TAG)

changelog-version: ## Generate changelog section for specific version (usage: make changelog-version VERSION=v1.1.0)
	python3 tools/generate_changelog.py --version $(VERSION)

changelog-release-notes: ## Generate release notes for specific version (usage: make changelog-release-notes VERSION=v1.1.0)
	python3 tools/generate_changelog.py --version $(VERSION) --release-notes

setup-conventional-commits: ## Setup conventional commits template
	git config commit.template .gitmessage
	@echo "Conventional commit template configured"
	@echo "Use 'git commit' (without -m) to use the template"

release-patch: ## Create patch release (x.x.X)
	python3 tools/release.py patch

release-minor: ## Create minor release (x.X.0)
	python3 tools/release.py minor

release-major: ## Create major release (X.0.0)
	python3 tools/release.py major

release-dry-run: ## Show what a patch release would do (dry run)
	python3 tools/release.py patch --dry-run

version:      ## Show current version
	@python3 -c "import re; content=open('pyproject.toml').read(); print(re.search(r'version\\s*=\\s*\"([^\"]+)\"', content).group(1))"
