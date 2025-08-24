# Base image with Alpine Python, Firefox, and geckodriver
# This can be reused across multiple projects that need web automation
FROM python:3.11-alpine

LABEL maintainer="oaklight"
LABEL description="Alpine Python base image with Firefox and geckodriver for web automation"

# Install runtime dependencies for Firefox and Selenium
RUN apk add --no-cache \
    firefox \
    dbus \
    ttf-freefont \
    wget \
    && rm -rf /var/cache/apk/*

# Install geckodriver
ARG GECKODRIVER_VERSION=0.36.0
RUN wget -q -O /tmp/geckodriver.tar.gz \
    "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && rm /tmp/geckodriver.tar.gz

# Install basic Selenium and web automation dependencies
COPY docker/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

# Create non-root user for security (common pattern)
RUN addgroup -g 1000 appuser && \
    adduser -D -s /bin/sh -u 1000 -G appuser appuser

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
