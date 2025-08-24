# Use our base image directly
FROM oaklight/alpine-python-gecko:latest

# Switch to root to install package
USER root

# Install the package from PyPI
RUN pip install --no-cache-dir tello-renewal

# Switch back to non-root user
USER appuser

# Default command
CMD ["tello-renewal", "--help"]