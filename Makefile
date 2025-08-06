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

## [Docker Compose]
up:           ## Start containers in background
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) up -d

down:         ## Stop and remove containers, networks, volumes
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) down

restart:      ## Restart containers
	$(MAKE) down
	$(MAKE) up

build:        ## Build the Docker images
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) build

pull:         ## Pull the latest images
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) pull

ps:           ## List running containers
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) ps

logs:         ## Tail logs from all services
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) logs -f

shell:        ## Open a shell in the default service (SERVICE=app)
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $(SERVICE) sh

sh: shell     ## Alias for `make shell`

shell-%:      ## Open a shell in specific service: make shell-maas or shell-db
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $* sh

## [Testing - Docker]
test-docker:  ## Run all tests inside Docker container
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $(SERVICE) pytest

test-docker-unit: ## Run unit tests inside Docker container
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $(SERVICE) pytest tests/unit/ -m "not slow"

test-docker-cov: ## Run tests with coverage inside Docker container
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) exec $(SERVICE) pytest --cov=src/hwautomation --cov-report=term-missing

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
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) build

ci-test:      ## CI test task with coverage
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) run --rm $(SERVICE) pytest --cov=src/hwautomation --cov-report=xml

ci-clean:     ## CI cleanup task
	docker-compose $(COMPOSE_FILES) --env-file $(ENV_FILE) -p $(PROJECT_NAME) down -v --remove-orphans

## [Development]
dev-setup:    ## Setup development environment
	cp .env.example .env || echo "Create .env file manually"
	pip install -e .[dev]
	$(MAKE) build

dev-reset:    ## Reset development environment
	$(MAKE) ci-clean
	$(MAKE) clean-test
	$(MAKE) dev-setup
