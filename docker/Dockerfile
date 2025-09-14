# Use our base image directly
FROM oaklight/alpine-python-gecko:latest

# Accept version as build argument - defaults to empty which will install latest from PyPI
ARG TELLO_VERSION

# Switch to root to install package
USER root

# Install the specific version of the package from PyPI
# If TELLO_VERSION is not specified, pip will install the latest version
RUN if [ -n "$TELLO_VERSION" ]; then \
        echo "Installing tello-renewal version: $TELLO_VERSION"; \
        pip install --no-cache-dir tello-renewal==$TELLO_VERSION; \
    else \
        echo "Installing latest tello-renewal from PyPI"; \
        pip install --no-cache-dir tello-renewal; \
    fi

# Switch back to non-root user
USER appuser

# Default command
CMD ["tello-renewal", "--help"]