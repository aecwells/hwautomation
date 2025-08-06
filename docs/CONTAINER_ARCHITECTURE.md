# Container Architecture Documentation

## Overview

HWAutomation has been optimized for container-first deployment with a production-ready architecture that prioritizes the web GUI interface while maintaining full CLI capabilities.

## Container Structure

### Multi-Stage Dockerfile (`Dockerfile.web`)

The application uses a multi-stage Docker build with the following targets:

1. **Base Stage**: Common dependencies and system packages
2. **Development Stage**: Development tools and editable install
3. **Production Stage**: Optimized for production deployment
4. **Web Stage**: GUI-first deployment (default)
5. **CLI Stage**: Command-line tool deployment

### Entry Points

#### Web Application (`webapp.py`)
- **Purpose**: Production-ready Flask web server entry point
- **Features**: 
  - Environment-based configuration
  - Comprehensive health monitoring
  - Production logging
  - Container-optimized settings
- **Usage**: Primary entry point for container deployment

#### Package Commands
- `hw-gui` / `hw-web`: Web interface launcher
- `hwautomation`: Traditional CLI tool

## Service Architecture

### Core Services

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| Web GUI | `hwautomation-app` | 5000 | Primary web interface |
| Database | `hwautomation-db` | 5432 | PostgreSQL data storage |
| Cache | `hwautomation-redis` | 6379 | Redis caching layer |
| DB Admin | `hwautomation-adminer` | 8080 | Database administration |
| Cache UI | `hwautomation-redis-ui` | 8081 | Redis monitoring |

### Health Monitoring

The web application includes comprehensive health checks:

```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "maas": "healthy", 
    "bios_manager": "healthy",
    "workflow_manager": "healthy",
    "device_types": 87,
    "maas_machines": 5,
    "active_workflows": 0
  },
  "timestamp": "2025-08-06T17:03:36.223282",
  "version": "1.0.0"
}
```

## Deployment Commands

### Using Docker Make Wrapper

The `docker-make` script handles Docker group permissions automatically:

```bash
# Start all services
./docker-make up

# Build containers  
./docker-make build

# View status
./docker-make ps

# View logs
./docker-make logs app

# Access shell
./docker-make shell app

# Stop services
./docker-make down
```

### Direct Docker Compose

```bash
# Start services
docker compose up -d

# Build with specific target
docker compose build --target web

# Health check
curl http://localhost:5000/health
```

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `FLASK_HOST` | `0.0.0.0` | Web server bind address |
| `FLASK_PORT` | `5000` | Web server port |
| `FLASK_DEBUG` | `false` | Debug mode (development only) |
| `PYTHONPATH` | `/app/src` | Python module path |

### Volume Mounts

- Application code: `/app` (development mode)
- Excluded: `/app/hwautomation-env` (virtual environment)

## Production Considerations

### Scaling

- Web tier can be horizontally scaled behind load balancer
- Database uses persistent volumes for data retention
- Redis provides shared session/cache storage

### Security

- Non-root user (`hwautomation`) in containers
- Network isolation through Docker networks
- Environment-based secrets management

### Monitoring

- Built-in health endpoints for orchestration
- Container health checks with 30s intervals
- Service dependency validation

## Development Workflow

### Local Development

1. Use override configuration for development features
2. Volume mount source code for live reloading
3. Access development tools through container shell

### Production Deployment

1. Build production target: `docker compose build --target production`
2. Use environment-specific configuration
3. Enable health check monitoring
4. Configure persistent storage volumes

## Migration from CLI-First

The architecture maintains backward compatibility:

- CLI tools remain available via `hwautomation` command
- All original functionality preserved
- GUI provides enhanced dashboard and management features
- Container deployment optimized for web-first usage

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Ensure ports 5000, 5432, 6379, 8080, 8081 are available
2. **Permission Issues**: Use `docker-make` wrapper or add user to docker group
3. **Health Check Failures**: Check service dependencies and network connectivity

### Debugging Commands

```bash
# Check container status
./docker-make ps

# View application logs
./docker-make logs app

# Access container shell
./docker-make shell app

# Test health endpoint
curl http://localhost:5000/health

# Monitor resource usage
docker stats
```

## Architecture Benefits

### Container-First Design
- Optimized for container orchestration
- Production-ready out of the box
- Scalable service architecture

### GUI-First Approach  
- Web interface as primary entry point
- Enhanced user experience
- Modern dashboard features

### Development Efficiency
- Multi-stage builds reduce image size
- Development/production parity
- Automated health monitoring

### Operational Excellence
- Comprehensive logging
- Health check integration
- Service dependency management
