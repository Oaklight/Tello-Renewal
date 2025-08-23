# Makefile for tello-renewal package

# Variables
PACKAGE_NAME := tello-renewal
DIST_DIR := dist
DOCKER_IMAGE := oaklight/tello-renewal
VERSION := $(shell python -c "import urllib.request, json; response = urllib.request.urlopen('https://pypi.org/pypi/$(PACKAGE_NAME)/json'); data = json.loads(response.read()); print(data['info']['version'])" 2>/dev/null || python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

# Default target
all: build push clean

# Build the Python package
build: clean
	@echo "Building $(PACKAGE_NAME) package..."
	python -m build
	@echo "Build complete. Distribution files are in $(DIST_DIR)/"

# Push the package to PyPI
push:
	@echo "Pushing $(PACKAGE_NAME) to PyPI..."
	twine upload $(DIST_DIR)/*
	@echo "Package pushed to PyPI."

# Clean up build and distribution files
clean:
	@echo "Cleaning up build and distribution files..."
	rm -rf $(DIST_DIR) *.egg-info build/
	@echo "Cleanup complete."

# Build Docker image
docker-build:
	@echo "Building Docker image $(DOCKER_IMAGE):$(VERSION) and $(DOCKER_IMAGE):latest..."
	./scripts/build.sh $(VERSION)

# Run Docker container with default settings
docker-run:
	@echo "Running Docker container..."
	./scripts/run.sh --help

# Clean Docker images and containers
docker-clean:
	@echo "Cleaning Docker images and containers..."
	docker rmi $(DOCKER_IMAGE):latest 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(VERSION) 2>/dev/null || true
	docker system prune -f

# Help target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Python package targets:"
	@echo "  build        - Build the Python package"
	@echo "  push         - Push the package to PyPI"
	@echo "  clean        - Clean up build and distribution files"
	@echo ""
	@echo "Docker targets:"
	@echo "  docker-build - Build Docker image using scripts/build.sh"
	@echo "  docker-run   - Show Docker run help"
	@echo "  docker-clean - Clean Docker images and containers"
	@echo ""
	@echo "General:"
	@echo "  help         - Show this help message"

.PHONY: all build push clean docker-build docker-run docker-clean help