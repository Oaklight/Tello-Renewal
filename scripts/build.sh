#!/bin/bash
set -e

# Build script for Tello Renewal Docker image

# Function to get version from PyPI or fallback to pyproject.toml
get_version() {
    # Try to get version from PyPI first
    PYPI_VERSION=$(python -c "
import urllib.request
import json
import sys
try:
    response = urllib.request.urlopen('https://pypi.org/pypi/tello-renewal/json')
    data = json.loads(response.read())
    print(data['info']['version'])
except Exception:
    sys.exit(1)
" 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$PYPI_VERSION" ]; then
        echo "$PYPI_VERSION"
    else
        # Fallback to pyproject.toml
        python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])"
    fi
}

# Get version from argument or fetch from PyPI/pyproject.toml
if [ -n "$1" ]; then
    VERSION="$1"
    echo "🔧 Using provided version: $VERSION"
else
    VERSION=$(get_version)
    PYPI_VERSION=$(python -c "
import urllib.request
import json
import sys
try:
    response = urllib.request.urlopen('https://pypi.org/pypi/tello-renewal/json')
    data = json.loads(response.read())
    print(data['info']['version'])
except Exception:
    pass
" 2>/dev/null)
    
    if [ -n "$PYPI_VERSION" ]; then
        echo "📦 Using PyPI version: $VERSION"
    else
        echo "⚠️  PyPI not available, using local version: $VERSION"
    fi
fi

IMAGE_NAME="oaklight/tello-renewal"

echo "🐳 Building Tello Renewal Docker image..."
echo "📦 Version: $VERSION"

# Build the image with version tag
docker build -f docker/Dockerfile -t "${IMAGE_NAME}:${VERSION}" .

# Tag as latest
docker tag "${IMAGE_NAME}:${VERSION}" "${IMAGE_NAME}:latest"

# Get image size
IMAGE_SIZE=$(docker images "${IMAGE_NAME}:latest" --format "table {{.Size}}" | tail -n 1)

echo "✅ Build completed successfully!"
echo "📦 Image size: $IMAGE_SIZE"
echo "🏷️  Tags: ${IMAGE_NAME}:${VERSION}, ${IMAGE_NAME}:latest"
echo ""
echo "Available commands:"
echo "  docker run --rm ${IMAGE_NAME}:latest tello-renewal --help"
echo "  docker-compose up tello-renewal"
echo ""
echo "Next steps:"
echo "1. Create config directory: mkdir -p config logs"
echo "2. Copy your config.toml to config/ directory"
echo "3. Run: docker-compose up tello-renewal"