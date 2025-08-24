# Docker Guide

[中文版](README_zh.md) | [English Version](README_en.md)

This document describes how to use Docker to run the Tello Renewal system and provides information about reusable base images.

## 🐳 Image Features

- **Base Image**: Alpine Linux (minimal)
- **Python Version**: 3.11
- **Browser**: Firefox + Geckodriver
- **Image Size**: ~150MB (estimated)
- **Security**: Non-root user execution
- **Resource Limits**: 512MB memory, 0.5 CPU cores

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+ (optional)
- At least 512MB available memory

## 🏗️ Base Images

### Alpine Python Gecko Base Image

The `base.Dockerfile` creates a reusable base image with:

- **Alpine Linux** - Minimal, secure base OS
- **Python 3.11** - Latest stable Python version
- **Firefox** - Headless browser for web automation
- **Geckodriver** - WebDriver for Firefox automation
- **Selenium** - Pre-installed web automation framework
- **Non-root user** - Security best practices

#### Image Details

- **Image Name**: `oaklight/alpine-python-gecko:latest`
- **Base**: `python:3.11-alpine`
- **User**: `appuser` (UID: 1000, GID: 1000)
- **Working Directory**: `/app`
- **Environment Variables**:
  - `DISPLAY=:99`
  - `MOZ_HEADLESS=1`

#### Pre-installed Dependencies

The base image includes this Python package:

- `selenium>=4.15.0` - Web automation framework

#### Building the Base Image

```bash
# Build the base image
make docker-build-base

# Push to DockerHub
make docker-push-base
```

#### Using in Other Projects

```dockerfile
FROM oaklight/alpine-python-gecko:latest

# Switch to root for installations
USER root

# Install your Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application
COPY . .
RUN chown -R appuser:appuser /app

# Switch back to non-root user
USER appuser

# Your application command
CMD ["python", "your-app.py"]
```

#### Benefits

1. **Consistency** - Same environment across all projects
2. **Faster Builds** - Base dependencies are pre-installed
3. **Security** - Non-root user and minimal attack surface
4. **Reusability** - Can be used by multiple web automation projects
5. **Maintenance** - Single place to update common dependencies
6. **Ready-to-use** - Selenium pre-installed and ready for web automation

#### Geckodriver Version

The current geckodriver version is `0.36.0`. To update:

1. Modify the `GECKODRIVER_VERSION` ARG in `base.Dockerfile`
2. Rebuild and push the base image
3. Update dependent projects to use the new base image

## 🚀 Quick Start

### 1. Build Images

```bash
# Build base image first
make docker-build-base

# Build application image
make docker-build

# Or use build script
./scripts/build.sh
```

### 2. Prepare Configuration

```bash
# Create directories
mkdir -p config logs

# Create configuration file
tello-renewal config-init --output config/config.toml
# Edit configuration file
nano config/config.toml
```

### 3. Run Container

```bash
# Use run script (recommended)
./scripts/run.sh

# Or use docker-compose
docker-compose up tello-renewal

# Or use docker run directly
docker run --rm \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  oaklight/tello-renewal:latest \
  tello-renewal --config /app/config/config.toml renew
```

## 📖 Usage

### Basic Commands

```bash
# Execute renewal
./scripts/run.sh

# Dry run mode (testing)
./scripts/run.sh --dry-run

# Check account status
./scripts/run.sh --command status

# Validate configuration
./scripts/run.sh --command config-validate

# Test email notifications
./scripts/run.sh --command email-test
```

### Docker Compose Method

```bash
# Single run
docker-compose up tello-renewal

# Background run
docker-compose up -d tello-renewal

# View logs
docker-compose logs -f tello-renewal

# Stop container
docker-compose down
```

### Scheduled Task Mode

```bash
# Start scheduled task (runs daily at 9 AM)
docker-compose --profile scheduler up -d tello-scheduler

# Custom time (daily at 6 AM)
CRON_SCHEDULE="0 6 * * *" docker-compose --profile scheduler up -d tello-scheduler

# View scheduled task logs
docker-compose logs -f tello-scheduler
```

## ⚙️ Configuration

### Directory Structure

```
project/
├── config/
│   └── config.toml          # Main configuration file
├── logs/                    # Log output directory
├── scripts/                 # Run scripts
├── docker-compose.yml       # Docker Compose configuration
└── docker/
    ├── Dockerfile          # Application image definition
    ├── base.Dockerfile     # Base image definition
    └── requirements.txt    # Base dependencies
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `America/Chicago` | Timezone setting |
| `CRON_SCHEDULE` | `0 9 * * *` | Scheduled task time |
| `CONFIG_FILE` | `/app/config/config.toml` | Configuration file path |

### Configuration File Example

```toml
[tello]
email = "your_email@example.com"
password = "your_password"
card_expiration = "1/25"  # MM/YY format

[browser]
browser_type = "firefox"
headless = true
window_size = "1920x1080"

[smtp]
server = "smtp.gmail.com"
port = 587
username = "your_email@gmail.com"
password = "your_app_password"
from_email = '"Tello Renewal" <your_email@gmail.com>'

[notifications]
email_enabled = true
recipients = ["admin@example.com"]
```

## 🔧 Troubleshooting

### Common Issues

1. **Configuration file not found**
   ```bash
   # Check configuration file path
   ls -la config/
   # Ensure config.toml exists
   ```

2. **Browser startup failure**
   ```bash
   # Check container logs
   docker-compose logs tello-renewal
   # Ensure sufficient memory
   ```

3. **Permission issues**
   ```bash
   # Check directory permissions
   chmod 755 config logs
   chmod 644 config/config.toml
   ```

### Debug Mode

```bash
# Enable verbose logging
docker run --rm \
  -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/logs:/app/logs \
  oaklight/tello-renewal:latest \
  tello-renewal --config /app/config/config.toml --verbose renew --dry-run

# Enter container for debugging
docker run -it --rm \
  -v $(pwd)/config:/app/config:ro \
  oaklight/tello-renewal:latest \
  sh
```

## 🔒 Security Recommendations

1. **Configuration file permissions**
   ```bash
   chmod 600 config/config.toml  # Owner read/write only
   ```

2. **Use app passwords**
   - Gmail: Use app-specific passwords
   - Avoid using main account passwords

3. **Network isolation**
   ```yaml
   # Add to docker-compose.yml
   networks:
     - tello-network
   ```

4. **Regular updates**
   ```bash
   # Update images
   docker pull python:3.11-alpine
   make docker-build-base
   make docker-build
   ```

## 📊 Monitoring and Logs

### Log Files

- `logs/tello_renewal.log` - Application logs
- `logs/cron.log` - Scheduled task logs

### Health Checks

```bash
# Check container status
docker-compose ps

# View health status
docker inspect tello-renewal | grep Health -A 10
```

### Resource Monitoring

```bash
# View resource usage
docker stats tello-renewal

# View container information
docker inspect tello-renewal
```

## 🔄 Updates and Maintenance

### Update Application

```bash
# Rebuild images
make docker-build-base
make docker-build

# Restart container
docker-compose down
docker-compose up -d tello-renewal
```

### Backup Configuration

```bash
# Backup configuration and logs
tar -czf tello-backup-$(date +%Y%m%d).tar.gz config/ logs/
```

### Cleanup

```bash
# Clean unused images
docker image prune

# Clean all unused resources
docker system prune -a

# Use Makefile cleanup
make docker-clean
```

## 📞 Support

If you encounter issues, please:

1. Check log files
2. Verify configuration is correct
3. Check GitHub Issues
4. Submit a new Issue with logs attached

---

**Note**: Please ensure compliance with Tello's terms of service and use this automation tool responsibly.