# Jhakaas Worker

AI worker service for face-preserving style transfer using InstantID and SDXL.

## Overview

This service provides a FastAPI-based worker that processes images through AI pipelines to apply artistic styles while preserving facial features. It uses InstantID for face preservation and SDXL for style transfer with LoRA adapters.

## Directory Structure

- **src/** - Core worker source code (FastAPI app, model manager, utilities)
- **tests/** - Test suite for integration and unit testing
- **deployment/** - Docker images, Cloud Build configs, and deployment files
- **models/** - Model download scripts and management

## Key Features

- Face-preserving style transfer (InstantID)
- Multiple artistic style support via LoRA adapters
- Health monitoring and graceful degradation
- Cloud Run deployment ready
- Automated model caching and management

## Quick Start

See [deployment/README.md](deployment/README.md) for deployment instructions.

## Testing

See [tests/README.md](tests/README.md) for testing documentation.
