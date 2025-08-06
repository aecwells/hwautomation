# Multi-stage Dockerfile for HWAutomation

# Base stage with Python and system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    openssh-client \
    iputils-ping \
    net-tools \
    ipmitool \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r hwautomation && useradd -r -g hwautomation hwautomation

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt requirements-all.txt pyproject.toml ./

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements-all.txt && \
    pip install pytest pytest-cov pytest-mock pytest-xdist pytest-html black flake8 mypy

# Copy source code
COPY . .

# Install package in development mode
RUN pip install -e .[dev]

# Change ownership to non-root user
RUN chown -R hwautomation:hwautomation /app
USER hwautomation

# Default command for development
CMD ["python", "main.py"]

# Testing stage
FROM development as testing

# Switch back to root to install testing tools
USER root

# Install additional testing dependencies
RUN pip install coverage[toml] pytest-benchmark pytest-timeout

# Switch back to non-root user
USER hwautomation

# Run tests by default
CMD ["pytest", "--cov=src/hwautomation", "--cov-report=xml", "--cov-report=term-missing"]

# Production stage
FROM base as production

# Install only production dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config.yaml main.py ./

# Install package
RUN pip install .

# Change ownership to non-root user
RUN chown -R hwautomation:hwautomation /app
USER hwautomation

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import hwautomation; print('OK')" || exit 1

# Default command for production
CMD ["python", "main.py"]
