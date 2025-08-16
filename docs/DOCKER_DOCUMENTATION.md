# Docker Deployment with Sphinx Documentation

## Overview

The HWAutomation system is fully containerized with Docker and includes automatic Sphinx documentation building during the container build process.

## Docker Architecture

### Multi-stage Build Process
The `docker/Dockerfile.web` includes:

1. **Base Stage**: System dependencies (Node.js, Python, ipmitool, etc.)
2. **Development Stage**: Development dependencies + testing tools
3. **Production Stage**: Production dependencies + frontend build + **documentation build**
4. **Web Stage**: Final web application container
5. **CLI Stage**: Command-line interface container

### Documentation Build in Container
```dockerfile
# Production stage automatically builds documentation
RUN cd docs && make html
```

The documentation is built **inside the container** during the Docker build process, ensuring:
- Documentation is always available when the container runs
- No need for manual documentation building
- Consistent documentation across deployments

## Deployment Commands

### Development with Docker Compose
```bash
# Start all services (includes automatic doc building)
docker-compose up --build

# Access the application
open http://localhost:5000

# Access documentation through web GUI
open http://localhost:5000/docs/
```

### Production Deployment
```bash
# Build production container
docker build -f docker/Dockerfile.web --target web -t hwautomation:latest .

# Run production container
docker run -d \
  --name hwautomation \
  -p 5000:5000 \
  -v $(pwd)/configs:/app/configs:ro \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  hwautomation:latest
```

## Container Documentation Access

### Web GUI Access
- **URL**: `http://localhost:5000/docs/`
- **Built-in**: Documentation is served directly from the Flask application
- **No External Server**: No need for separate documentation hosting

### Container Paths
- **Source Documentation**: `/app/docs/` (Markdown + RST files)
- **Built Documentation**: `/app/docs/_build/html/` (Generated HTML)
- **Web Route**: Flask serves from `/app/docs/_build/html/` at `/docs/` endpoint

### Volume Mounting
The `docker-compose.yml` mounts the project directory:
```yaml
volumes:
  - .:/app  # Mounts entire project including docs/
```

This allows:
- Live documentation updates during development
- Documentation source files available in container
- Built documentation persists across container restarts

## Container Environment Variables

### Documentation-Specific
```env
# No special environment variables needed
# Documentation paths are automatic in container
```

### Required for Web Application
```env
PYTHONPATH=/app/src
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
HWAUTOMATION_MODE=web
```

## Build Process Flow

1. **Container Build**: `docker-compose up --build`
2. **Install Dependencies**: Python + Node.js packages
3. **Build Frontend**: `npm run build` (Vite assets)
4. **Build Documentation**: `cd docs && make html` (Sphinx HTML)
5. **Install Package**: `pip install .`
6. **Start Application**: Flask web server with `/docs/` routes

## Troubleshooting Docker Documentation

### Check Documentation in Container
```bash
# Access running container
docker exec -it hwautomation-app bash

# Verify documentation files
ls -la /app/docs/_build/html/

# Check Flask routes
curl http://localhost:5000/docs/
```

### Rebuild Documentation in Container
```bash
# If documentation needs updating
docker exec -it hwautomation-app bash
cd /app/docs
make clean
make html
```

### Container Logs
```bash
# Check application logs
docker logs hwautomation-app

# Look for documentation-related errors
docker logs hwautomation-app 2>&1 | grep -i "docs\|sphinx\|documentation"
```

## Production Considerations

### Documentation Caching
- Documentation is built **once** during container build
- No runtime documentation building overhead
- Static HTML files served directly by Flask

### Security
- Documentation served from internal Flask routes
- No external web server needed
- Same authentication/security as main application

### Performance
- HTML files served directly from container filesystem
- No external calls or database queries for documentation
- Fast serving with proper HTTP headers

### Updates
To update documentation in production:
1. Update source documentation files
2. Rebuild container: `docker-compose up --build`
3. Deploy new container image

## Development Workflow

### Live Documentation Development
```bash
# Run development container with live reload
docker-compose up

# In another terminal, rebuild docs on changes
docker exec -it hwautomation-app bash
cd /app/docs
make html

# Refresh browser to see changes
```

### Local Development Alternative
```bash
# If developing documentation locally
make docs-serve  # Serves on http://localhost:8080
```

## Container Health Checks

The web container includes health checks that verify:
- Flask application is running
- Web routes are responsive
- Documentation endpoint is accessible

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1
```

## Summary

The Sphinx documentation system is fully integrated into the Docker deployment:

✅ **Automatic Build**: Documentation built during container build
✅ **Web Integration**: Served at `/docs/` endpoint in main application
✅ **No External Dependencies**: No separate documentation server needed
✅ **Production Ready**: Optimized for container deployment
✅ **Development Friendly**: Live updates during development
✅ **Secure**: Same security model as main application
