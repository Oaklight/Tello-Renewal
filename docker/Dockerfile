# Use our base image directly
FROM oaklight/alpine-python-gecko:latest

# Accept version as build argument - defaults to empty which will install latest from PyPI
ARG TELLO_VERSION
# Accept local wheel file path as build argument
ARG LOCAL_WHEEL
# Accept PyPI mirror as optional build argument
ARG PYPI_MIRROR

# Switch to root to install package
USER root

# Create temporary directory for potential local wheels
RUN mkdir -p /tmp/dist/

# Copy the entire project context and extract dist if it exists
COPY . /tmp/build/
RUN if [ -d "/tmp/build/dist" ] && [ "$(ls -A /tmp/build/dist 2>/dev/null)" ]; then \
        cp /tmp/build/dist/*.whl /tmp/dist/ 2>/dev/null || true; \
    fi && \
    rm -rf /tmp/build/

# Install the package - prioritize local wheel, then specific version, then latest from PyPI
RUN if [ -n "$LOCAL_WHEEL" ] && [ -f "/tmp/dist/$LOCAL_WHEEL" ]; then \
        echo "Installing from local wheel: $LOCAL_WHEEL"; \
        if [ -n "$PYPI_MIRROR" ]; then \
            pip install -i "$PYPI_MIRROR" --no-cache-dir "/tmp/dist/$LOCAL_WHEEL"; \
        else \
            pip install --no-cache-dir "/tmp/dist/$LOCAL_WHEEL"; \
        fi; \
    elif [ -n "$TELLO_VERSION" ]; then \
        echo "Installing tello-renewal version: $TELLO_VERSION"; \
        if [ -n "$PYPI_MIRROR" ]; then \
            pip install -i "$PYPI_MIRROR" --no-cache-dir tello-renewal==$TELLO_VERSION; \
        else \
            pip install --no-cache-dir tello-renewal==$TELLO_VERSION; \
        fi; \
    else \
        echo "Installing latest tello-renewal from PyPI"; \
        if [ -n "$PYPI_MIRROR" ]; then \
            pip install -i "$PYPI_MIRROR" --no-cache-dir tello-renewal; \
        else \
            pip install --no-cache-dir tello-renewal; \
        fi; \
    fi && \
    rm -rf /tmp/dist/

# Switch back to non-root user
USER appuser

# Default command
CMD ["tello-renewal", "--help"]