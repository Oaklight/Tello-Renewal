# Tello-Renewal

[![Docker Image Version](https://img.shields.io/docker/v/oaklight/tello-renewal?label=Docker&logo=docker)](https://hub.docker.com/r/oaklight/tello-renewal)
[![PyPI version](https://badge.fury.io/py/tello-renewal.svg?icon=si%3Apython)](https://badge.fury.io/py/tello-renewal)
[![GitHub version](https://badge.fury.io/gh/oaklight%2FTello-Renewal.svg?icon=si%3Agithub)](https://badge.fury.io/gh/oaklight%2FTello-Renewal)

[中文版](README_zh.md) | [English Version](README_en.md)

Automatic renewal system for Tello mobile plans using web automation.

## Features

- 🔄 Automatic plan renewal using Selenium web automation
- 📧 Email notifications for success/failure
- 🧪 Dry run mode for testing
- ⚙️ TOML configuration with validation
- 🔒 Secure credential handling
- 📊 Comprehensive logging
- 🐳 Docker support with reusable base images

## Installation

### From Source

```bash
# Clone the repository
git clone <repository-url>
cd tello-renewal

# Install in development mode
pip install -e .

# Or install from PyPI (when published)
pip install tello-renewal
```

### Requirements

- Python 3.10+
- Firefox, Chrome, or Edge browser
- WebDriver for your chosen browser (geckodriver for Firefox)

## Quick Start

1. **Create configuration file:**

   ```bash
   tello-renewal config-init
   ```

2. **Edit the configuration:**

   ```bash
   # Edit config.toml with your settings
   nano config.toml
   ```

3. **Test your configuration:**

   ```bash
   # Validate configuration
   tello-renewal config-validate

   # Test email notifications
   tello-renewal email-test

   # Check account status
   tello-renewal status
   ```

4. **Run renewal (dry run first):**

   ```bash
   # Test renewal without actually renewing
   tello-renewal renew --dry-run

   # Perform actual renewal
   tello-renewal renew
   ```

## Configuration

The system uses TOML configuration files. Here's a minimal example:

```toml
[tello]
email = "your_email@example.com"
password = "your_password"
card_expiration = "1/25"  # MM/YY format

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

### Configuration Sections

- **`[tello]`** - Tello account credentials and settings
- **`[browser]`** - Browser automation settings
- **`[renewal]`** - Renewal behavior configuration
- **`[smtp]`** - Email server settings
- **`[notifications]`** - Notification preferences
- **`[logging]`** - Logging configuration

## CLI Commands

### Basic Operations

```bash
# Execute renewal
tello-renewal renew [--dry-run]

# Check account status and balance information
tello-renewal status
```

### Configuration Management

```bash
# Create example configuration
tello-renewal config-init [--output config.toml]

# Validate configuration
tello-renewal config-validate
```

### Testing

```bash
# Test email notifications
tello-renewal email-test
```

### Options

- `--config, -c` - Specify configuration file path
- `--verbose, -v` - Enable verbose logging
- `--help` - Show help information

## Exit Codes

| Code | Meaning             |
| ---- | ------------------- |
| 0    | Success             |
| 1    | General error       |
| 2    | Configuration error |
| 5    | Renewal failed      |
| 6    | Not due for renewal |

## Scheduling

### Cron Job

Add to your crontab to run daily:

```bash
# Run daily at 9 AM
0 9 * * * /path/to/venv/bin/tello-renewal renew

# With logging
0 9 * * * /path/to/venv/bin/tello-renewal renew >> /var/log/tello-renewal.log 2>&1
```

### Systemd Service

Create `/etc/systemd/system/tello-renewal.service`:

```ini
[Unit]
Description=Tello Plan Auto Renewal
After=network.target

[Service]
Type=oneshot
User=tello
WorkingDirectory=/opt/tello-renewal
ExecStart=/opt/tello-renewal/venv/bin/tello-renewal renew
```

Create `/etc/systemd/system/tello-renewal.timer`:

```ini
[Unit]
Description=Run Tello renewal daily
Requires=tello-renewal.service

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl enable tello-renewal.timer
sudo systemctl start tello-renewal.timer
```

## Security Considerations

- Store sensitive configuration files with restricted permissions (600)
- Use app passwords for email authentication
- Consider encrypting configuration files containing passwords
- Run with minimal privileges
- Regularly update dependencies

## Troubleshooting

### Common Issues

1. **WebDriver not found:**

   ```bash
   # Install geckodriver for Firefox
   # On Ubuntu/Debian:
   sudo apt install firefox-geckodriver

   # On macOS:
   brew install geckodriver
   ```

2. **Login failures:**

   - Verify credentials in configuration
   - Check if Tello website structure has changed
   - Try running with `--verbose` for detailed logs

3. **Email sending failures:**

   - Verify SMTP settings
   - Use app passwords for Gmail
   - Test with `tello-renewal email-test`

4. **Browser automation issues:**
   - Try different browser types in configuration
   - Disable headless mode for debugging
   - Check browser and WebDriver versions

### Debug Mode

Run with verbose logging to troubleshoot issues:

```bash
tello-renewal --verbose renew --dry-run
```

### Log Files

Check log files for detailed error information:

```bash
tail -f tello_renewal.log
```

## Docker Usage

For detailed Docker usage instructions, see [`docker/README_en.md`](docker/README_en.md) or [`docker/README_zh.md`](docker/README_zh.md).

### Quick Docker Start

```bash
# Build and run with Docker
make build-docker
docker run --rm -v $(pwd)/config:/app/config oaklight/tello-renewal:latest

# Or use the provided scripts
./scripts/run.sh --help
```

### Available Docker Commands

```bash
# Build base image (Alpine Python + Selenium + geckodriver)
make build-docker-base
make push-docker-base

# Build application image
make build-docker
make push-docker

# Build with specific version
make build-docker V=1.0.0

# Build with PyPI mirror
make build-docker MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple

# Package management
make build-package
make push-package
make clean-package

# Clean up
make clean-docker
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd tello-renewal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tello_renewal

# Run specific test file
pytest tests/test_models.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is provided as-is for educational and automation purposes. Users are responsible for:

- Ensuring compliance with Tello's terms of service
- Maintaining the security of their credentials
- Monitoring the renewal process
- Having backup payment methods available

The authors are not responsible for any service interruptions, failed renewals, or other issues that may arise from using this software.
