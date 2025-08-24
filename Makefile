# Makefile for tello-renewal package

# Variables
PACKAGE_NAME := tello-renewal
DIST_DIR := dist
DOCKER_IMAGE := oaklight/tello-renewal
BASE_IMAGE := oaklight/alpine-python-gecko
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

# Build base Docker image
docker-build-base:
	@echo "Building base Docker image $(BASE_IMAGE):latest..."
	docker build -f docker/base.Dockerfile -t $(BASE_IMAGE):latest .
	@echo "Base image built successfully."

# Build Docker image
docker-build:
	@echo "Building Docker image $(DOCKER_IMAGE):$(VERSION) and $(DOCKER_IMAGE):latest..."
	./scripts/build.sh $(VERSION)

# Push base Docker image to DockerHub
docker-push-base:
	@echo "Pushing base Docker image $(BASE_IMAGE):latest to DockerHub..."
	docker push $(BASE_IMAGE):latest
	@echo "Base Docker image pushed to DockerHub."

# Push Docker image to DockerHub
docker-push:
	@echo "Pushing Docker image $(DOCKER_IMAGE):$(VERSION) and $(DOCKER_IMAGE):latest to DockerHub..."
	docker push $(DOCKER_IMAGE):$(VERSION)
	docker push $(DOCKER_IMAGE):latest
	@echo "Docker images pushed to DockerHub."

# Run Docker container with default settings
docker-run:
	@echo "Running Docker container..."
	./scripts/run.sh --help

# Clean Docker images and containers
docker-clean:
	@echo "Cleaning Docker images and containers..."
	docker rmi $(DOCKER_IMAGE):latest 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(VERSION) 2>/dev/null || true
	docker rmi $(BASE_IMAGE):latest 2>/dev/null || true
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
	@echo "  docker-build-base - Build base Docker image with Alpine Python + geckodriver"
	@echo "  docker-push-base  - Push base Docker image to DockerHub"
	@echo "  docker-build      - Build Docker image using scripts/build.sh"
	@echo "  docker-push       - Push Docker image to DockerHub"
	@echo "  docker-run        - Show Docker run help"
	@echo "  docker-clean      - Clean Docker images and containers"
	@echo ""
	@echo "General:"
	@echo "  help         - Show this help message"

.PHONY: all build push clean docker-build-base docker-push-base docker-build docker-push docker-run docker-clean help