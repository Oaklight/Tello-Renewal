# Multi-stage build for minimal image size
FROM python:3.11-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev

# Create virtual environment and install Python dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the package from PyPI
RUN pip install --no-cache-dir tello-renewal

# Production stage
FROM python:3.11-alpine

# Install runtime dependencies for Firefox and Selenium
RUN apk add --no-cache \
    firefox \
    dbus \
    ttf-freefont \
    && rm -rf /var/cache/apk/*

# Install geckodriver
RUN wget -q -O /tmp/geckodriver.tar.gz \
    "https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz" \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN addgroup -g 1000 tello && \
    adduser -D -s /bin/sh -u 1000 -G tello tello

# Create directories for configuration and logs
RUN mkdir -p /app/config /app/logs && \
    chown -R tello:tello /app

# Switch to non-root user
USER tello
WORKDIR /app

# Set environment variables for headless operation
ENV DISPLAY=:99
ENV MOZ_HEADLESS=1

# Default command
CMD ["tello-renewal", "--help"]