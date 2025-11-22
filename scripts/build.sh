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

# Parse command line arguments
VERSION_ARG=""
PYPI_MIRROR=""

while [[ $# -gt 0 ]]; do
	case $1 in
	--mirror)
		PYPI_MIRROR="$2"
		shift 2
		;;
	--mirror=*)
		PYPI_MIRROR="${1#*=}"
		shift
		;;
	*)
		if [ -z "$VERSION_ARG" ]; then
			VERSION_ARG="$1"
		fi
		shift
		;;
	esac
done

# Check for local wheel file first
LOCAL_WHEEL=""
BUILD_ARGS=""

if [ -d "dist" ] && [ -n "$(ls -A dist/*.whl 2>/dev/null)" ]; then
	LOCAL_WHEEL=$(ls dist/*.whl | head -n 1 | xargs basename)
	VERSION=$(echo "$LOCAL_WHEEL" | sed 's/tello_renewal-\(.*\)-py3-none-any.whl/\1/')
	echo "🎯 Found local wheel: $LOCAL_WHEEL"
	echo "📦 Using local version: $VERSION"
	BUILD_ARGS="--build-arg LOCAL_WHEEL=${LOCAL_WHEEL}"
elif [ -n "$VERSION_ARG" ]; then
	VERSION="$VERSION_ARG"
	echo "🔧 Using provided version: $VERSION"
	# When version is explicitly provided, pass it as build arg
	BUILD_ARGS="--build-arg TELLO_VERSION=${VERSION}"
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
		echo "📦 Using latest PyPI version: $VERSION"
		# Don't pass build arg, let Docker install latest from PyPI
		BUILD_ARGS=""
	else
		echo "⚠️  PyPI not available, using local version: $VERSION"
		# Pass the local version as build arg
		BUILD_ARGS="--build-arg TELLO_VERSION=${VERSION}"
	fi
fi

# Add PyPI mirror to build args if specified
if [ -n "$PYPI_MIRROR" ]; then
	BUILD_ARGS="$BUILD_ARGS --build-arg PYPI_MIRROR=${PYPI_MIRROR}"
	echo "🌐 Using PyPI mirror: $PYPI_MIRROR"
fi

IMAGE_NAME="oaklight/tello-renewal"

echo "🐳 Building Tello Renewal Docker image..."
echo "📦 Version: $VERSION"

# Build the image with version tag, conditionally passing version as build argument
docker build -f docker/Dockerfile $BUILD_ARGS -t "${IMAGE_NAME}:${VERSION}" .

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
echo "Usage examples:"
echo "  ./scripts/build.sh                                    # Build latest version"
echo "  ./scripts/build.sh 1.0.0                             # Build specific version"
echo "  ./scripts/build.sh --mirror https://pypi.tuna.tsinghua.edu.cn/simple"
echo "  ./scripts/build.sh 1.0.0 --mirror https://mirrors.cernet.edu.cn/pypi/web/simple"
echo ""
echo "Next steps:"
echo "1. Create config directory: mkdir -p config logs"
echo "2. Copy your config.toml to config/ directory"
echo "3. Run: docker-compose up tello-renewal"
