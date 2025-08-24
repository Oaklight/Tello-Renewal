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

# Production stage - use our base image
FROM oaklight/alpine-python-gecko:latest

# Switch to root to copy files and set permissions
USER root

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Ensure proper ownership
RUN chown -R appuser:appuser /opt/venv

# Switch back to non-root user
USER appuser

# Default command
CMD ["tello-renewal", "--help"]