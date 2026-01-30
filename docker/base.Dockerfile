# Base image with Alpine Python, Firefox, and geckodriver
# This can be reused across multiple projects that need web automation
ARG REGISTRY_MIRROR=docker.io
FROM ${REGISTRY_MIRROR}/python:3.11-alpine

LABEL maintainer="oaklight"
LABEL description="Alpine Python base image with Firefox and geckodriver for web automation"

# Install runtime dependencies, geckodriver, and setup user in single layer
ARG GECKODRIVER_VERSION=0.36.0
RUN apk add --no-cache \
    firefox \
    dbus \
    ttf-freefont \
    wget \
    && wget -q -O /tmp/geckodriver.tar.gz \
    "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && pip install --no-cache-dir selenium>=4.27.0 \
    && addgroup -g 1000 appuser \
    && adduser -D -s /bin/sh -u 1000 -G appuser appuser \
    && apk del wget \
    && rm -rf /tmp/* /var/cache/apk/*

# Set environment variables for headless operation
ENV DISPLAY=:99
ENV MOZ_HEADLESS=1

# Create common directories
RUN mkdir -p /app/config /app/logs && \
    chown -R appuser:appuser /app

WORKDIR /app
USER appuser

# Default command
CMD ["/bin/sh"]
