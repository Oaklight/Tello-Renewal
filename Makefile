# Makefile for tello-renewal package

# Variables
PACKAGE_NAME := tello-renewal
DIST_DIR := dist
DOCKER_IMAGE := oaklight/tello-renewal
BASE_IMAGE := oaklight/alpine-python-gecko
VERSION := $(shell python -c "import urllib.request, json; response = urllib.request.urlopen('https://pypi.org/pypi/$(PACKAGE_NAME)/json'); data = json.loads(response.read()); print(data['info']['version'])" 2>/dev/null || python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

# Optional variables
V ?= $(VERSION)
MIRROR ?=

# Build the Python package
build-package: clean-package
	@echo "Building $(PACKAGE_NAME) package..."
	python -m build
	@echo "Build complete. Distribution files are in $(DIST_DIR)/"

# Push the package to PyPI
push-package:
	@echo "Pushing $(PACKAGE_NAME) to PyPI..."
	twine upload $(DIST_DIR)/*
	@echo "Package pushed to PyPI."

# Clean up build and distribution files
clean-package:
	@echo "Cleaning up build and distribution files..."
	rm -rf $(DIST_DIR) *.egg-info build/
	@echo "Cleanup complete."

# Build Docker image
build-docker:
	@echo "Building Docker image $(DOCKER_IMAGE):$(V)..."
	@if [ -n "$(MIRROR)" ]; then \
		echo "Using PyPI mirror: $(MIRROR)"; \
		./scripts/build.sh $(V) --mirror $(MIRROR); \
	else \
		./scripts/build.sh $(V); \
	fi
	@echo "Docker image built successfully."

# Push Docker image to DockerHub
push-docker:
	@echo "Pushing Docker image $(DOCKER_IMAGE):$(V) and $(DOCKER_IMAGE):latest to DockerHub..."
	docker push $(DOCKER_IMAGE):$(V)
	docker push $(DOCKER_IMAGE):latest
	@echo "Docker images pushed to DockerHub."

# Clean Docker images and containers
clean-docker:
	@echo "Cleaning Docker images and containers..."
	docker rmi $(DOCKER_IMAGE):latest 2>/dev/null || true
	docker rmi $(DOCKER_IMAGE):$(V) 2>/dev/null || true
	docker rmi $(BASE_IMAGE):latest 2>/dev/null || true
	docker system prune -f

# Help target
help:
	@echo "Available targets:"
	@echo ""
	@echo "Package targets:"
	@echo "  build-package  - Build the Python package"
	@echo "  push-package   - Push the package to PyPI"
	@echo "  clean-package  - Clean up build and distribution files"
	@echo ""
	@echo "Docker targets:"
	@echo "  build-docker   - Build Docker image"
	@echo "  push-docker    - Push Docker image to DockerHub"
	@echo "  clean-docker   - Clean Docker images and containers"
	@echo ""
	@echo "Usage examples:"
	@echo "  make build-docker                                    # Build with auto-detected version"
	@echo "  make build-docker V=1.0.0                          # Build with specific version"
	@echo "  make build-docker MIRROR=https://pypi.tuna.tsinghua.edu.cn/simple"
	@echo "  make build-docker V=1.0.0 MIRROR=https://mirrors.cernet.edu.cn/pypi/web/simple"
	@echo ""
	@echo "Variables:"
	@echo "  V=<version>    - Specify version (default: auto-detected)"
	@echo "  MIRROR=<url>   - Specify PyPI mirror URL"

.PHONY: build-package push-package clean-package build-docker push-docker clean-docker help