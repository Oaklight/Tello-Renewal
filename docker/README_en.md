# Docker Guide

[中文版](README_zh.md) | [English Version](README_en.md)

This document describes how to use Docker to run the Tello Renewal system and provides information about reusable base images.

## 🐳 Image Features

- **Base Image**: Alpine Linux (minimal)
- **Python Version**: 3.11
- **Browser**: Firefox + Geckodriver
- **Image Size**: ~831MB (base image)
- **Security**: Non-root user execution
- **Resource Limits**: 512MB memory, 0.5 CPU cores

## 📋 Prerequisites

- Docker 20.10+
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

- `selenium>=4.27.0` - Web automation framework

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

### 3. Download and Run

```bash
# Download run script
curl -o run.sh https://raw.githubusercontent.com/Oaklight/Tello-Renewal/refs/heads/master/scripts/run.sh
chmod +x run.sh

# Use run script (recommended)
./run.sh renew

# Or use docker run directly
docker run --rm \
  -v ~/.config/tello-renewal:/app/config:ro \
  -v ./logs:/app/logs \
  -e TZ=America/Chicago \
  oaklight/tello-renewal:latest \
  tello-renewal --config /app/config/config.toml renew
```

### Alternative Download URLs

If GitHub is not accessible, use these mirror URLs:

```bash
# JSDelivr CDN
curl -o run.sh https://cdn.jsdelivr.net/gh/Oaklight/Tello-Renewal@master/scripts/run.sh

# JSDelivr Mirror
curl -o run.sh https://cdn.jsdmirror.com/gh/Oaklight/Tello-Renewal@master/scripts/run.sh
```

## 📖 Usage

### Basic Commands

```bash
# Execute renewal
./run.sh renew

# Dry run mode (testing)
./run.sh renew --dry-run

# Check account status
./run.sh status

# Validate configuration
./run.sh config-validate

# Test email notifications
./run.sh email-test

# Create example configuration
./run.sh config-init --output ~/.config/tello-renewal/config.toml
```

### Scheduled Task with Cron

Set up automatic renewal using system cron:

```bash
# Edit crontab
crontab -e

# Add daily renewal at 9 AM (adjust path as needed)
0 9 * * * /path/to/run.sh renew >> /var/log/tello-renewal-cron.log 2>&1

# Or weekly renewal on Sundays at 9 AM
0 9 * * 0 /path/to/run.sh renew >> /var/log/tello-renewal-cron.log 2>&1
```

### Advanced Cron Setup

```bash
# Create a dedicated script for cron
cat > /usr/local/bin/tello-renewal-cron.sh << 'EOF'
#!/bin/bash
cd /path/to/your/project
./run.sh renew
EOF

chmod +x /usr/local/bin/tello-renewal-cron.sh

# Add to crontab
echo "0 9 * * * /usr/local/bin/tello-renewal-cron.sh" | crontab -
```

## ⚙️ Configuration

### Directory Structure

```
project/
├── ~/.config/tello-renewal/
│   └── config.toml          # Main configuration file
├── logs/                    # Log output directory
└── run.sh                   # Run script
```

### Environment Variables

| Variable      | Default                   | Description             |
| ------------- | ------------------------- | ----------------------- |
| `TZ`          | `America/Chicago`         | Timezone setting        |
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
   # Check logs directory
   ls -la logs/
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
