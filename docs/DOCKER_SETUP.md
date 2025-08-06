# Docker Compose Setup for HWAutomation

This document explains how to set up and use the Docker Compose environment for HWAutomation development and testing.

## Prerequisites

### Install Docker and Docker Compose

#### Ubuntu/Debian:
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply group changes
```

#### macOS:
```bash
# Install Docker Desktop from https://docker.com/products/docker-desktop
# Docker Compose is included with Docker Desktop
```

#### Verify Installation:
```bash
docker --version
docker-compose --version
```

## Quick Start

1. **Setup Environment**:
   ```bash
   make dev-setup
   ```

2. **Start Development Environment**:
   ```bash
   make up
   ```

3. **View Running Services**:
   ```bash
   make ps
   ```

4. **Run Tests in Docker**:
   ```bash
   make test-docker
   ```

5. **Open Shell in Container**:
   ```bash
   make shell
   ```

6. **Stop Environment**:
   ```bash
   make down
   ```

## Available Services

### Core Services
- **app**: Main HWAutomation application
- **db**: PostgreSQL database for development
- **redis**: Redis for caching and task queues

### Development Tools
- **adminer**: Database management UI (http://localhost:8080)
- **redis-commander**: Redis management UI (http://localhost:8081)

### Testing Services (Profile: testing)
- **test**: Dedicated testing container
- **maas-simulator**: MaaS simulation for testing

## Environment Configuration

Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

Key environment variables:
- `PROJECT_NAME`: Docker Compose project name (default: hwautomation)
- `DEBUG`: Enable debug mode
- `DB_*`: Database configuration
- `MAAS_*`: MaaS connection settings

## Docker Compose Profiles

### Default Profile
Starts core services for development:
```bash
make up
```

### Testing Profile
Includes additional testing services:
```bash
docker-compose --profile testing up -d
```

## Available Make Commands

### Local Testing
- `make test`: Run tests locally
- `make test-unit`: Run unit tests locally
- `make test-cov`: Run tests with coverage locally

### Docker Operations
- `make up`: Start all services
- `make down`: Stop all services
- `make build`: Build Docker images
- `make logs`: View container logs
- `make shell`: Open shell in app container
- `make ps`: List running containers

### Docker Testing
- `make test-docker`: Run all tests in Docker
- `make test-docker-unit`: Run unit tests in Docker
- `make test-docker-cov`: Run tests with coverage in Docker

### CI/CD
- `make ci-build`: CI build task
- `make ci-test`: CI test task
- `make ci-clean`: CI cleanup task

### Development
- `make dev-setup`: Setup development environment
- `make dev-reset`: Reset development environment

## File Structure

```
├── docker-compose.yml          # Main compose configuration
├── docker-compose.override.yml # Development overrides
├── Dockerfile                  # Multi-stage Docker build
├── .env.example               # Environment template
├── .dockerignore              # Docker ignore patterns
└── Makefile                   # Enhanced with Docker support
```

## Docker Architecture

### Multi-Stage Dockerfile
- **base**: Common Python environment
- **development**: Development dependencies + tools
- **testing**: Testing-specific setup
- **production**: Minimal production image

### Networking
- All services communicate via `hwautomation` network
- External ports mapped for development access

### Data Persistence
- `postgres_data`: Database data
- `redis_data`: Redis data
- `maas_data`: MaaS simulator data

## Development Workflow

1. **Start Environment**:
   ```bash
   make up
   ```

2. **Code Changes**: 
   - Local files are mounted into containers
   - Changes reflect immediately

3. **Run Tests**:
   ```bash
   make test-docker-unit  # Fast unit tests
   make test-docker-cov   # With coverage
   ```

4. **Access Services**:
   - App: http://localhost:5000
   - Database UI: http://localhost:8080
   - Redis UI: http://localhost:8081

5. **Debug**:
   ```bash
   make shell              # Enter app container
   make logs               # View all logs
   make shell-db           # Enter database container
   ```

## Testing Strategy

### Local vs Docker Testing
- **Local**: Fast development iteration
- **Docker**: Environment consistency, CI/CD pipeline

### Test Types
- **Unit Tests**: Fast, isolated, mocked dependencies
- **Integration Tests**: Real service interactions
- **End-to-End Tests**: Full workflow validation

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   ```bash
   make down
   docker-compose ps
   ```

2. **Permission Issues**:
   ```bash
   sudo chown -R $USER:$USER .
   ```

3. **Build Failures**:
   ```bash
   make clean-test
   docker system prune -a
   make build
   ```

4. **Database Issues**:
   ```bash
   docker-compose down -v  # Remove volumes
   make up
   ```

### Debug Commands
```bash
make debug              # Show environment variables
make ps                 # List containers
docker-compose logs app # Service-specific logs
```

## Production Deployment

For production deployment, use the production stage:

```dockerfile
# Build production image
docker build --target production -t hwautomation:prod .

# Run production container
docker run -d \
  --name hwautomation-prod \
  -p 5000:5000 \
  -v /path/to/config.yaml:/app/config.yaml \
  hwautomation:prod
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` to version control
2. **Secrets Management**: Use Docker secrets for production
3. **Network Security**: Configure proper firewall rules
4. **User Permissions**: Containers run as non-root user
5. **Image Scanning**: Scan images for vulnerabilities

## Performance Optimization

1. **Multi-stage Builds**: Smaller production images
2. **Layer Caching**: Optimized Dockerfile layer order
3. **Volume Mounts**: Exclude unnecessary directories
4. **Resource Limits**: Configure CPU/memory limits
5. **Parallel Testing**: Use `pytest -n auto` for faster tests

## Integration with CI/CD

The setup integrates with GitHub Actions and other CI/CD systems:

```yaml
# Example GitHub Actions workflow
- name: Run Docker Tests
  run: |
    make ci-build
    make ci-test
    make ci-clean
```
