# Deployment Guide

Comprehensive deployment guide for HWAutomation covering containerization, database management, and production deployment strategies.

## 📋 Table of Contents

- [Overview](#-overview)
- [Container Architecture](#-container-architecture)
- [Deployment Options](#-deployment-options)
- [Database Management](#-database-management)
- [Production Deployment](#-production-deployment)
- [Monitoring & Health Checks](#-monitoring--health-checks)
- [Troubleshooting](#-troubleshooting)

## 🎯 Overview

HWAutomation is designed for container-first deployment with multiple deployment strategies:

- **Single Container**: Production-ready Flask web server with SQLite
- **Multi-Service**: Orchestrated deployment with external services
- **Development**: Local development with hot reload
- **Testing**: Isolated testing environment with simulators

### Key Features

- ✅ **Container-First Design**: Optimized for Docker and Kubernetes
- ✅ **SQLite Integration**: File-based database, no external DB required
- ✅ **Automatic Migrations**: Schema versioning and data preservation
- ✅ **Health Monitoring**: Comprehensive service health checks
- ✅ **Multi-Environment**: Development, testing, and production configs
- ✅ **Scalability**: Ready for horizontal scaling

## 🐳 Container Architecture

### Multi-Stage Dockerfile

The application uses a multi-stage Docker build (`docker/Dockerfile.web`):

```dockerfile
# Stage 1: Base dependencies
FROM python:3.11-slim AS base
# Common system packages and Python dependencies

# Stage 2: Development
FROM base AS development
# Development tools and editable installs

# Stage 3: Production
FROM base AS production
# Optimized for production deployment

# Stage 4: Web (Default)
FROM production AS web
# GUI-first deployment with Flask
EXPOSE 5000
CMD ["python", "-m", "hwautomation.web.app"]
```

### Service Architecture

| Service | Container | Port | Purpose | Database |
|---------|-----------|------|---------|----------|
| **Web GUI** | `hwautomation-app` | 5000 | Primary web interface | SQLite (integrated) |
| **MaaS Simulator** | `hwautomation-maas-sim` | 5240 | Testing environment | N/A |

**Note**: SQLite database is integrated within the main container - no separate database container required.

### Entry Points

**Command Options:**
- `hw-gui` / `hw-web`: Web interface launcher
- `hwautomation`: Traditional CLI tool
- `python -m hwautomation.web.app`: Direct Flask application

## 🚀 Deployment Options

### Option 1: Quick Start (Recommended)

```bash
# Clone repository
git clone https://github.com/your-org/hwautomation.git
cd hwautomation

# Start web interface
docker compose up -d app

# Access application
open http://localhost:5000
```

### Option 2: Full Docker Compose

```bash
# Start all services including testing
docker compose --profile testing up -d

# Production deployment
docker compose --profile production up -d

# View status
docker compose ps
```

### Option 3: Manual Docker Build

```bash
# Build production container
docker build -f docker/Dockerfile.web --target web -t hwautomation:latest .

# Run container
docker run -d \
  --name hwautomation-app \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  hwautomation:latest
```

### Option 4: Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hwautomation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: hwautomation
  template:
    metadata:
      labels:
        app: hwautomation
    spec:
      containers:
      - name: hwautomation
        image: hwautomation:latest
        ports:
        - containerPort: 5000
        env:
        - name: ENVIRONMENT
          value: "production"
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## 🗄️ Database Management

### SQLite Migration System

HWAutomation includes a robust database migration system:

#### Migration Features

- **Automatic Migrations**: Databases upgrade automatically on startup
- **Version Tracking**: Each migration tracked with version and timestamp
- **Backup Creation**: Automatic backups before applying migrations
- **Rollback Safety**: Migrations designed to be safe and reversible
- **Schema Export**: Export current schema for documentation
- **Data Integrity**: Preserves existing data during schema changes

#### Migration Versions

| Version | Name | Description |
|---------|------|-------------|
| **1** | Initial schema | Basic server tracking table |
| **2** | Add IPMI fields | IPMI credentials and Redfish support |
| **3** | Add timestamps | Created/updated/last seen tracking |
| **4** | Add metadata | CPU, memory, storage, rack location |
| **5** | Add power state | Power state tracking and history |

### Database Operations

**Automatic Migration (Recommended):**
```python
from hwautomation.database import DbHelper

# Database automatically migrated to latest version
db_helper = DbHelper('hw_automation.db', auto_migrate=True)
```

**Manual Migration Management:**
```bash
# Check database status
python -m hwautomation.database.db_manager status -d hw_automation.db

# Apply migrations
python -m hwautomation.database.db_manager migrate -d hw_automation.db

# Create backup
python -m hwautomation.database.db_manager backup -d hw_automation.db

# Initialize new database
python -m hwautomation.database.db_manager init -d new_database.db
```

**Container Database Management:**
```bash
# Access container shell
docker compose exec app bash

# Check database status inside container
python -m hwautomation.database.db_manager status

# Apply migrations
python -m hwautomation.database.db_manager migrate

# Backup database
python -m hwautomation.database.db_manager backup
```

### Schema Evolution

**Current Schema (Version 5):**
```sql
CREATE TABLE servers (
    server_id TEXT PRIMARY KEY,
    status_name TEXT,
    is_ready TEXT,
    server_model TEXT,
    ip_address TEXT,
    ip_address_works TEXT,

    -- Version 2: IPMI fields
    ipmi_ip TEXT,
    ipmi_username TEXT,
    ipmi_password TEXT,
    redfish_supported INTEGER DEFAULT 0,

    -- Version 3: Timestamps
    created_at TEXT,
    updated_at TEXT,
    last_seen TEXT,

    -- Version 4: Hardware metadata
    cpu_count INTEGER,
    memory_gb INTEGER,
    storage_tb REAL,
    rack_location TEXT,

    -- Version 5: Power state
    power_state TEXT,
    power_state_history TEXT
);

CREATE TABLE migration_history (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT
);
```

## 🏭 Production Deployment

### Environment Configuration

**Production Environment Variables:**
```bash
# Application settings
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export DATABASE_PATH=/app/data/hw_automation.db

# MaaS integration
export MAAS_URL=https://maas.company.com:5240/MAAS
export MAAS_CONSUMER_KEY=your_consumer_key
export MAAS_TOKEN_KEY=your_token_key
export MAAS_TOKEN_SECRET=your_token_secret

# Security settings
export SECRET_KEY=your_production_secret_key
export FLASK_ENV=production

# Performance settings
export WORKERS=4
export TIMEOUT=120
```

**Docker Compose Production:**
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  app:
    build:
      context: .
      dockerfile: docker/Dockerfile.web
      target: web
    ports:
      - "5000:5000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_PATH=/app/data/hw_automation.db
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
      - ./configs:/app/configs:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Reverse Proxy Configuration

**Nginx Configuration:**
```nginx
# /etc/nginx/sites-available/hwautomation
upstream hwautomation {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name hwautomation.company.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name hwautomation.company.com;

    ssl_certificate /etc/ssl/certs/hwautomation.crt;
    ssl_certificate_key /etc/ssl/private/hwautomation.key;

    # Main application
    location / {
        proxy_pass http://hwautomation;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://hwautomation;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files (if serving separately)
    location /static/ {
        alias /var/www/hwautomation/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Load Balancer Configuration

**HAProxy Configuration:**
```
# /etc/haproxy/haproxy.cfg
global
    daemon
    log stdout local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend hwautomation_frontend
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/hwautomation.pem
    redirect scheme https if !{ ssl_fc }
    default_backend hwautomation_backend

backend hwautomation_backend
    balance roundrobin
    option httpchk GET /health
    server app1 127.0.0.1:5001 check
    server app2 127.0.0.1:5002 check
    server app3 127.0.0.1:5003 check
```

### Container Orchestration

**Docker Swarm:**
```yaml
# docker-stack.yml
version: '3.8'
services:
  app:
    image: hwautomation:latest
    ports:
      - "5000:5000"
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    networks:
      - hwautomation-network
    volumes:
      - hwautomation-data:/app/data

volumes:
  hwautomation-data:
    driver: local

networks:
  hwautomation-network:
    driver: overlay
```

## 📊 Monitoring & Health Checks

### Health Check Endpoint

**Comprehensive Health Status:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "maas": "healthy",
    "bios_manager": "healthy",
    "workflow_manager": "healthy",
    "bios_device_types": 87,
    "maas_machines": 5,
    "active_workflows": 0
  },
  "timestamp": "2025-01-15T10:30:00Z",
  "version": "1.0.0",
  "database": {
    "path": "/app/data/hw_automation.db",
    "size_mb": 12.5,
    "version": 5,
    "last_migration": "2025-01-15T08:00:00Z"
  }
}
```

### Monitoring Integration

**Prometheus Metrics:**
```python
# Custom metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_prometheus_metrics()
```

**Docker Health Checks:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1
```

### Log Management

**Structured Logging:**
```python
import logging
import json

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/hwautomation.log'),
        logging.StreamHandler()
    ]
)
```

**Log Aggregation:**
```yaml
# docker-compose.logging.yml
version: '3.8'
services:
  app:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "localhost:24224"
        tag: "hwautomation.app"
```

## 🔧 Troubleshooting

### Common Deployment Issues

**Container Won't Start:**
```bash
# Check container logs
docker compose logs app

# Check system resources
docker system df
docker system prune

# Verify image build
docker images | grep hwautomation
```

**Database Connection Issues:**
```bash
# Access container and check database
docker compose exec app bash
ls -la /app/data/
python -m hwautomation.database.db_manager status

# Check database permissions
stat /app/data/hw_automation.db
```

**Port Conflicts:**
```bash
# Check port usage
netstat -tlnp | grep 5000
lsof -i :5000

# Use different port
docker compose up -d -e PORT=5001
```

### Performance Optimization

**Container Performance:**
```dockerfile
# Optimize Dockerfile
FROM python:3.11-slim AS base
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Multi-stage build for smaller images
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Use non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser
```

**Database Performance:**
```python
# SQLite optimizations
import sqlite3

# Enable WAL mode for better concurrency
conn = sqlite3.connect('hw_automation.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA synchronous=NORMAL')
conn.execute('PRAGMA cache_size=10000')
conn.execute('PRAGMA temp_store=MEMORY')
```

### Backup and Recovery

**Database Backup:**
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/app/backups"
DB_PATH="/app/data/hw_automation.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup
sqlite3 $DB_PATH ".backup $BACKUP_DIR/hw_automation_$TIMESTAMP.db"

# Compress backup
gzip "$BACKUP_DIR/hw_automation_$TIMESTAMP.db"

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

**Container Data Volumes:**
```bash
# Backup container volumes
docker run --rm \
  -v hwautomation_data:/source:ro \
  -v $(pwd)/backups:/backup \
  ubuntu tar czf /backup/hwautomation_data_$(date +%Y%m%d).tar.gz -C /source .

# Restore from backup
docker run --rm \
  -v hwautomation_data:/target \
  -v $(pwd)/backups:/backup \
  ubuntu tar xzf /backup/hwautomation_data_20250115.tar.gz -C /target
```

## 📚 Related Documentation

- **Getting Started**: `docs/GETTING_STARTED.md`
- **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
- **Hardware Management**: `docs/HARDWARE_MANAGEMENT.md`
- **Workflow Guide**: `docs/WORKFLOW_GUIDE.md`
- **API Reference**: `docs/API_REFERENCE.md`
